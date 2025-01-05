"""Device Handlers模块"""

import asyncio
import json
import logging
import os
import socket
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import boto3
import docker
import libvirt
import paramiko
import requests
from kubernetes import client, config
from models.user import Device, DeviceBackup
from pysnmp.hlapi.asyncio import *
from services.cache import cache

logger = logging.getLogger(__name__)


class BaseDeviceHandler:
    """设备处理器基类"""

    def __init__(self, device: Device):
        self.device = device
        self.credentials = self._get_credentials()

    def _get_credentials(self) -> Dict[str, str]:
        """获取设备凭证"""
        return self.device.config.get("credentials", {})

    async def test_connection(self) -> bool:
        """测试连接"""
        raise NotImplementedError

    async def backup(self, backup: DeviceBackup) -> bool:
        """执行备份"""
        raise NotImplementedError

    async def restore(self, backup: DeviceBackup) -> bool:
        """执行恢复"""
        raise NotImplementedError

    async def update(self, params: Dict[str, Any]) -> bool:
        """执行更新"""
        raise NotImplementedError

    async def collect_metrics(self) -> List[Dict[str, Any]]:
        """收集指标"""
        raise NotImplementedError


class NetworkDeviceHandler(BaseDeviceHandler):
    """网络设备处理器"""

    async def test_connection(self) -> bool:
        try:
            if self.device.subtype in ["router", "switch"]:
                # 使用SNMP测试连接
                engine = SnmpEngine()
                auth_data = UsmUserData(
                    self.credentials.get("username"),
                    authKey=self.credentials.get("auth_key"),
                    privKey=self.credentials.get("priv_key"),
                )
                target = UdpTransportTarget((self.device.ip_address, 161))

                # 获取系统描述
                result = await getNextRequestObject(
                    engine,
                    auth_data,
                    target,
                    ContextData(),
                    ObjectType(ObjectIdentity("SNMPv2-MIB", "sysDescr", 0)),
                )

                return bool(result)
            return False
        except Exception as e:
            logger.error(f"Network device connection test failed: {e}")
            return False

    async def backup(self, backup: DeviceBackup) -> bool:
        try:
            # 创建SSH客户端
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                self.device.ip_address,
                username=self.credentials.get("username"),
                password=self.credentials.get("password"),
            )

            # 根据设备类型执行不同的备份命令
            if self.device.manufacturer.lower() == "cisco":
                command = "show running-config"
            elif self.device.manufacturer.lower() == "huawei":
                command = "display current-configuration"
            else:
                raise ValueError(
                    f"Unsupported manufacturer: {self.device.manufacturer}"
                )

            # 执行命令并获取配置
            stdin, stdout, stderr = ssh.exec_command(command)
            config_data = stdout.read().decode()

            # 保存配置文件
            backup_path = f"backups/network/{self.device.id}/{backup.id}.conf"
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
            with open(backup_path, "w") as f:
                f.write(config_data)

            # 更新备份记录
            backup.backup_path = backup_path
            backup.file_size = len(config_data)
            backup.status = "completed"

            return True

        except Exception as e:
            logger.error(f"Network device backup failed: {e}")
            return False
        finally:
            ssh.close()

    async def collect_metrics(self) -> List[Dict[str, Any]]:
        metrics = []
        try:
            # 使用SNMP收集网络指标
            engine = SnmpEngine()
            auth_data = UsmUserData(
                self.credentials.get("username"),
                authKey=self.credentials.get("auth_key"),
                privKey=self.credentials.get("priv_key"),
            )
            target = UdpTransportTarget((self.device.ip_address, 161))

            # 收集接口流量
            for interface in range(1, 9):  # 假设有8个接口
                in_octets = await getNextRequestObject(
                    engine,
                    auth_data,
                    target,
                    ContextData(),
                    ObjectType(ObjectIdentity("IF-MIB", "ifInOctets", interface)),
                )
                out_octets = await getNextRequestObject(
                    engine,
                    auth_data,
                    target,
                    ContextData(),
                    ObjectType(ObjectIdentity("IF-MIB", "ifOutOctets", interface)),
                )

                metrics.extend(
                    [
                        {
                            "metric_type": "network_in",
                            "metric_name": f"interface_{interface}_in",
                            "value": str(in_octets.value),
                            "unit": "bytes",
                            "tags": {"interface": str(interface)},
                        },
                        {
                            "metric_type": "network_out",
                            "metric_name": f"interface_{interface}_out",
                            "value": str(out_octets.value),
                            "unit": "bytes",
                            "tags": {"interface": str(interface)},
                        },
                    ]
                )

            return metrics

        except Exception as e:
            logger.error(f"Network metrics collection failed: {e}")
            return []


class StorageDeviceHandler(BaseDeviceHandler):
    """存储设备处理器"""

    async def test_connection(self) -> bool:
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                self.device.ip_address,
                username=self.credentials.get("username"),
                password=self.credentials.get("password"),
            )
            ssh.close()
            return True
        except Exception as e:
            logger.error(f"Storage device connection test failed: {e}")
            return False

    async def backup(self, backup: DeviceBackup) -> bool:
        try:
            # 根据存储设备类型执行不同的备份操作
            if self.device.subtype == "nas":
                return await self._backup_nas(backup)
            elif self.device.subtype == "san":
                return await self._backup_san(backup)
            else:
                raise ValueError(f"Unsupported storage type: {self.device.subtype}")
        except Exception as e:
            logger.error(f"Storage device backup failed: {e}")
            return False

    async def collect_metrics(self) -> List[Dict[str, Any]]:
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                self.device.ip_address,
                username=self.credentials.get("username"),
                password=self.credentials.get("password"),
            )

            metrics = []

            # 获取存储容量信息
            stdin, stdout, stderr = ssh.exec_command("df -h")
            df_output = stdout.read().decode()

            for line in df_output.split("\n")[1:]:
                if line:
                    parts = line.split()
                    if len(parts) >= 5:
                        filesystem = parts[0]
                        size = parts[1]
                        used = parts[2]
                        available = parts[3]
                        use_percent = parts[4].rstrip("%")

                        metrics.extend(
                            [
                                {
                                    "metric_type": "disk",
                                    "metric_name": f"{filesystem}_size",
                                    "value": size,
                                    "unit": "GB",
                                    "tags": {"filesystem": filesystem},
                                },
                                {
                                    "metric_type": "disk",
                                    "metric_name": f"{filesystem}_used",
                                    "value": used,
                                    "unit": "GB",
                                    "tags": {"filesystem": filesystem},
                                },
                                {
                                    "metric_type": "disk",
                                    "metric_name": f"{filesystem}_usage",
                                    "value": use_percent,
                                    "unit": "%",
                                    "tags": {"filesystem": filesystem},
                                },
                            ]
                        )

            # 获取IO性能信息
            stdin, stdout, stderr = ssh.exec_command("iostat -x 1 1")
            iostat_output = stdout.read().decode()

            for line in iostat_output.split("\n"):
                if "avg-cpu" in line:
                    continue
                if line and not line.startswith("Device"):
                    parts = line.split()
                    if len(parts) >= 6:
                        device = parts[0]
                        r_iops = parts[3]
                        w_iops = parts[4]

                        metrics.extend(
                            [
                                {
                                    "metric_type": "iops",
                                    "metric_name": f"{device}_read_iops",
                                    "value": r_iops,
                                    "unit": "iops",
                                    "tags": {"device": device},
                                },
                                {
                                    "metric_type": "iops",
                                    "metric_name": f"{device}_write_iops",
                                    "value": w_iops,
                                    "unit": "iops",
                                    "tags": {"device": device},
                                },
                            ]
                        )

            return metrics

        except Exception as e:
            logger.error(f"Storage metrics collection failed: {e}")
            return []
        finally:
            ssh.close()


class VirtualizationHandler(BaseDeviceHandler):
    """虚拟化平台处理器"""

    def __init__(self, device: Device):
        super().__init__(device)
        self.conn = None

    async def test_connection(self) -> bool:
        try:
            if self.device.subtype == "vmware":
                # 实现VMware连接测试
                pass
            elif self.device.subtype == "kvm":
                uri = f"qemu \
                ssh://{self.credentials.get('username')}@{self.device.ip_address}/system"
                self.conn = libvirt.open(uri)
                return bool(self.conn)
            return False
        except Exception as e:
            logger.error(f"Virtualization platform connection test failed: {e}")
            return False

    async def collect_metrics(self) -> List[Dict[str, Any]]:
        try:
            metrics = []

            if self.device.subtype == "kvm":
                if not self.conn:
                    await self.test_connection()

                # 获取主机信息
                host_info = self.conn.getInfo()
                metrics.extend(
                    [
                        {
                            "metric_type": "cpu",
                            "metric_name": "host_cpu_count",
                            "value": str(host_info[2]),
                            "unit": "cores",
                            "tags": {"type": "host"},
                        },
                        {
                            "metric_type": "memory",
                            "metric_name": "host_memory_total",
                            "value": str(host_info[1]),
                            "unit": "MB",
                            "tags": {"type": "host"},
                        },
                    ]
                )

                # 获取所有虚拟机的资源使用情况
                for domain in self.conn.listAllDomains():
                    vm_name = domain.name()
                    vm_info = domain.info()

                    metrics.extend(
                        [
                            {
                                "metric_type": "cpu",
                                "metric_name": f"vm_{vm_name}_cpu_usage",
                                "value": str(vm_info[3]),
                                "unit": "%",
                                "tags": {"vm": vm_name},
                            },
                            {
                                "metric_type": "memory",
                                "metric_name": f"vm_{vm_name}_memory_usage",
                                "value": str(vm_info[2]),
                                "unit": "MB",
                                "tags": {"vm": vm_name},
                            },
                        ]
                    )

            return metrics

        except Exception as e:
            logger.error(f"Virtualization metrics collection failed: {e}")
            return []


class ContainerHandler(BaseDeviceHandler):
    """容器平台处理器"""

    def __init__(self, device: Device):
        super().__init__(device)
        self.client = None

    async def test_connection(self) -> bool:
        try:
            if self.device.subtype == "docker":
                self.client = docker.DockerClient(
                    base_url=f"tcp://{self.device.ip_address}:2375"
                )
                return bool(self.client.ping())
            elif self.device.subtype == "k8s":
                config.load_kube_config()
                self.client = client.CoreV1Api()
                self.client.list_namespace()
                return True
            return False
        except Exception as e:
            logger.error(f"Container platform connection test failed: {e}")
            return False

    async def collect_metrics(self) -> List[Dict[str, Any]]:
        try:
            metrics = []

            if self.device.subtype == "docker":
                if not self.client:
                    await self.test_connection()

                # 获取所有容器的资源使用情况
                for container in self.client.containers.list():
                    stats = container.stats(stream=False)

                    # CPU使用率
                    cpu_delta = (
                        stats["cpu_stats"]["cpu_usage"]["total_usage"]
                        - stats["precpu_stats"]["cpu_usage"]["total_usage"]
                    )
                    system_delta = (
                        stats["cpu_stats"]["system_cpu_usage"]
                        - stats["precpu_stats"]["system_cpu_usage"]
                    )
                    cpu_usage = (cpu_delta / system_delta) * 100

                    # 内存使用率
                    memory_usage = stats["memory_stats"]["usage"]
                    memory_limit = stats["memory_stats"]["limit"]
                    memory_percent = (memory_usage / memory_limit) * 100

                    metrics.extend(
                        [
                            {
                                "metric_type": "cpu",
                                "metric_name": f"container_{container.name}_cpu_usage",
                                "value": str(cpu_usage),
                                "unit": "%",
                                "tags": {"container": container.name},
                            },
                            {
                                "metric_type": "memory",
                                "metric_name": f"container_{container.name}_memory_usage",
                                "value": str(memory_percent),
                                "unit": "%",
                                "tags": {"container": container.name},
                            },
                        ]
                    )

            elif self.device.subtype == "k8s":
                if not self.client:
                    await self.test_connection()

                # 获取所有Pod的资源使用情况
                pods = self.client.list_pod_for_all_namespaces()
                metrics_api = client.CustomObjectsApi()

                for pod in pods.items:
                    try:
                        pod_metrics = metrics_api.get_namespaced_custom_object(
                            "metrics.k8s.io",
                            "v1beta1",
                            pod.metadata.namespace,
                            "pods",
                            pod.metadata.name,
                        )

                        for container in pod_metrics["containers"]:
                            cpu = container["usage"]["cpu"]
                            memory = container["usage"]["memory"]

                            metrics.extend(
                                [
                                    {
                                        "metric_type": "cpu",
                                        "metric_name": f"pod_{pod.metadata.name}_"
                                        f'{container["name"]}_cpu_usage',
                                        "value": cpu,
                                        "unit": "cores",
                                        "tags": {
                                            "pod": pod.metadata.name,
                                            "container": container["name"],
                                            "namespace": pod.metadata.namespace,
                                        },
                                    },
                                    {
                                        "metric_type": "memory",
                                        "metric_name": f"pod_{pod.metadata.name}_"
                                        f'{container["name"]}_memory_usage',
                                        "value": memory,
                                        "unit": "bytes",
                                        "tags": {
                                            "pod": pod.metadata.name,
                                            "container": container["name"],
                                            "namespace": pod.metadata.namespace,
                                        },
                                    },
                                ]
                            )
                    except Exception as e:
                        logger.error(
                            f"Failed to get metrics for pod {pod.metadata.name}: {e}"
                        )

            return metrics

        except Exception as e:
            logger.error(f"Container metrics collection failed: {e}")
            return []


class LoadBalancerHandler(BaseDeviceHandler):
    """负载均衡器处理器"""

    async def test_connection(self) -> bool:
        try:
            # 使用SNMP或HTTP API测试连接
            if self.device.manufacturer.lower() == "f5":
                # 使用F5 iControl REST API
                url = f"https://{self.device.ip_address}/mgmt/tm/sys/version"
                response = requests.get(
                    url,
                    auth=(
                        self.credentials.get("username"),
                        self.credentials.get("password"),
                    ),
                    verify=False,
                )
                return response.status_code == 200
            elif self.device.manufacturer.lower() == "haproxy":
                # 使用HAProxy Stats Socket
                stats_socket = self.device.config.get("stats_socket")
                if stats_socket:
                    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                        s.connect(stats_socket)
                        return True
            return False
        except Exception as e:
            logger.error(f"Load balancer connection test failed: {e}")
            return False

    async def collect_metrics(self) -> List[Dict[str, Any]]:
        try:
            metrics = []

            if self.device.manufacturer.lower() == "f5":
                # 收集F5指标
                url = f"https://{self.device.ip_address}/mgmt/tm/sys/performance/all-stat \
                          \
                          \
                          \
                          \
                          \
                         s"
                response = requests.get(
                    url,
                    auth=(
                        self.credentials.get("username"),
                        self.credentials.get("password"),
                    ),
                    verify=False,
                )
                stats = response.json()

                # CPU使用率
                metrics.append(
                    {
                        "metric_type": "cpu",
                        "metric_name": "cpu_usage",
                        "value": stats["entries"]["systemCpu"]["value"],
                        "unit": "%",
                        "tags": {"type": "system"},
                    }
                )

                # 连接数
                metrics.append(
                    {
                        "metric_type": "connections",
                        "metric_name": "active_connections",
                        "value": stats["entries"]["clientSideTraffic"]["value"][
                            "current_connections"
                        ],
                        "unit": "count",
                        "tags": {"type": "client"},
                    }
                )

            elif self.device.manufacturer.lower() == "haproxy":
                # 收集HAProxy指标
                stats_socket = self.device.config.get("stats_socket")
                if stats_socket:
                    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
                        s.connect(stats_socket)
                        s.send(b"show stat\n")
                        data = s.recv(8192).decode()

                        for line in data.split("\n"):
                            if line and not line.startswith("#"):
                                fields = line.split(",")
                                if len(fields) > 30:
                                    proxy_name = fields[0]
                                    status = fields[17]
                                    current_conn = fields[4]

                                    metrics.extend(
                                        [
                                            {
                                                "metric_type": "connections",
                                                "metric_name": f"{proxy_name}_connections",
                                                "value": current_conn,
                                                "unit": "count",
                                                "tags": {"proxy": proxy_name},
                                            }
                                        ]
                                    )

            return metrics

        except Exception as e:
            logger.error(f"Load balancer metrics collection failed: {e}")
            return []


class FirewallHandler(BaseDeviceHandler):
    """防火墙处理器"""

    async def test_connection(self) -> bool:
        try:
            if self.device.manufacturer.lower() == "paloalto":
                # 使用PAN-OS XML API
                url = f"https://{self.device.ip_address}/api"
                params = {
                    "type": "op",
                    "cmd": "<show><system><info></info></system></show>",
                    "key": self.credentials.get("api_key"),
                }
                response = requests.get(url, params=params, verify=False)
                return response.status_code == 200
            elif self.device.manufacturer.lower() == "fortinet":
                # 使用FortiOS REST API
                url = f"https://{self.device.ip_address}/api/v2/monitor/system/status"
                headers = {"Authorization": f"Bearer {self.credentials.get('api_key')}"}
                response = requests.get(url, headers=headers, verify=False)
                return response.status_code == 200
            return False
        except Exception as e:
            logger.error(f"Firewall connection test failed: {e}")
            return False

    async def collect_metrics(self) -> List[Dict[str, Any]]:
        try:
            metrics = []

            if self.device.manufacturer.lower() == "paloalto":
                # 收集PAN-OS指标
                url = f"https://{self.device.ip_address}/api"
                params = {
                    "type": "op",
                    "cmd": "<show><system><resources></resources></system></show>",
                    "key": self.credentials.get("api_key"),
                }
                response = requests.get(url, params=params, verify=False)
                data = response.json()

                # CPU使用率
                metrics.append(
                    {
                        "metric_type": "cpu",
                        "metric_name": "cpu_usage",
                        "value": data["response"]["result"]["cpu"],
                        "unit": "%",
                        "tags": {"type": "system"},
                    }
                )

                # 会话数
                metrics.append(
                    {
                        "metric_type": "sessions",
                        "metric_name": "active_sessions",
                        "value": data["response"]["result"]["session"]["active"],
                        "unit": "count",
                        "tags": {"type": "active"},
                    }
                )

            elif self.device.manufacturer.lower() == "fortinet":
                # 收集FortiOS指标
                url = f"https://{self.device.ip_address}/api/v2/monitor/system/resource/u \
                          \
                          \
                          \
                          \
                          \
                         sage"
                headers = {"Authorization": f"Bearer {self.credentials.get('api_key')}"}
                response = requests.get(url, headers=headers, verify=False)
                data = response.json()

                metrics.extend(
                    [
                        {
                            "metric_type": "cpu",
                            "metric_name": "cpu_usage",
                            "value": data["results"]["cpu"],
                            "unit": "%",
                            "tags": {"type": "system"},
                        },
                        {
                            "metric_type": "memory",
                            "metric_name": "memory_usage",
                            "value": data["results"]["memory"],
                            "unit": "%",
                            "tags": {"type": "system"},
                        },
                        {
                            "metric_type": "sessions",
                            "metric_name": "active_sessions",
                            "value": data["results"]["sessions"],
                            "unit": "count",
                            "tags": {"type": "active"},
                        },
                    ]
                )

            return metrics

        except Exception as e:
            logger.error(f"Firewall metrics collection failed: {e}")
            return []


class SDNControllerHandler(BaseDeviceHandler):
    """SDN控制器处理器"""

    async def test_connection(self) -> bool:
        try:
            if self.device.subtype == "opendaylight":
                # 使用OpenDaylight RESTCONF API
                url = f"http://{self.device.ip_address}:8181/restconf/operational/network \
                          \
                          \
                          \
                          \
                          \
                         -topology:network-topology"
                auth = (
                    self.credentials.get("username"),
                    self.credentials.get("password"),
                )
                response = requests.get(url, auth=auth)
                return response.status_code == 200
            elif self.device.subtype == "onos":
                # 使用ONOS REST API
                url = f"http://{self.device.ip_address}:8181/onos/v1/devices"
                auth = (
                    self.credentials.get("username"),
                    self.credentials.get("password"),
                )
                response = requests.get(url, auth=auth)
                return response.status_code == 200
            return False
        except Exception as e:
            logger.error(f"SDN controller connection test failed: {e}")
            return False

    async def collect_metrics(self) -> List[Dict[str, Any]]:
        try:
            metrics = []

            if self.device.subtype == "opendaylight":
                # 收集OpenDaylight指标
                base_url = f"http://{self.device.ip_address}:8181/restconf/operational"
                auth = (
                    self.credentials.get("username"),
                    self.credentials.get("password"),
                )

                # 获取拓扑信息
                topology_url = f"{base_url}/network-topology:network-topology"
                response = requests.get(topology_url, auth=auth)
                topology_data = response.json()

                # 统计节点和链路
                nodes = 0
                links = 0
                for topology in topology_data["network-topology"]["topology"]:
                    nodes += len(topology.get("node", []))
                    links += len(topology.get("link", []))

                metrics.extend(
                    [
                        {
                            "metric_type": "topology",
                            "metric_name": "node_count",
                            "value": nodes,
                            "unit": "count",
                            "tags": {"type": "node"},
                        },
                        {
                            "metric_type": "topology",
                            "metric_name": "link_count",
                            "value": links,
                            "unit": "count",
                            "tags": {"type": "link"},
                        },
                    ]
                )

            elif self.device.subtype == "onos":
                # 收集ONOS指标
                base_url = f"http://{self.device.ip_address}:8181/onos/v1"
                auth = (
                    self.credentials.get("username"),
                    self.credentials.get("password"),
                )

                # 获取设备信息
                devices_response = requests.get(f"{base_url}/devices", auth=auth)
                devices_data = devices_response.json()

                # 获取流表信息
                flows_response = requests.get(f"{base_url}/flows", auth=auth)
                flows_data = flows_response.json()

                metrics.extend(
                    [
                        {
                            "metric_type": "devices",
                            "metric_name": "device_count",
                            "value": len(devices_data["devices"]),
                            "unit": "count",
                            "tags": {"type": "device"},
                        },
                        {
                            "metric_type": "flows",
                            "metric_name": "flow_count",
                            "value": len(flows_data["flows"]),
                            "unit": "count",
                            "tags": {"type": "flow"},
                        },
                    ]
                )

            return metrics

        except Exception as e:
            logger.error(f"SDN controller metrics collection failed: {e}")
            return []


class CloudPlatformHandler(BaseDeviceHandler):
    """云平台处理器"""

    def __init__(self, device: Device):
        super().__init__(device)
        self.client = None

    async def test_connection(self) -> bool:
        try:
            if self.device.subtype == "openstack":
                # 使用OpenStack API
                from keystoneauth1 import session
                from keystoneauth1.identity import v3
                from novaclient import client as nova_client

                auth = v3.Password(
                    auth_url=self.device.config["auth_url"],
                    username=self.credentials.get("username"),
                    password=self.credentials.get("password"),
                    project_name=self.device.config["project_name"],
                    user_domain_id="default",
                    project_domain_id="default",
                )
                sess = session.Session(auth=auth)
                self.client = nova_client.Client(2, session=sess)
                return bool(self.client.servers.list(limit=1))

            elif self.device.subtype == "aws":
                # 使用AWS API
                import boto3

                self.client = boto3.client(
                    "ec2",
                    aws_access_key_id=self.credentials.get("access_key"),
                    aws_secret_access_key=self.credentials.get("secret_key"),
                    region_name=self.device.config["region"],
                )
                self.client.describe_instances(MaxResults=1)
                return True

            return False
        except Exception as e:
            logger.error(f"Cloud platform connection test failed: {e}")
            return False

    async def collect_metrics(self) -> List[Dict[str, Any]]:
        try:
            metrics = []

            if self.device.subtype == "openstack":
                if not self.client:
                    await self.test_connection()

                # 获取计算资源使用情况
                hypervisors = self.client.hypervisors.list()
                for hypervisor in hypervisors:
                    metrics.extend(
                        [
                            {
                                "metric_type": "cpu",
                                "metric_name": f"hypervisor_{hypervisor.id}_cpu_usage",
                                "value": hypervisor.cpu_usage,
                                "unit": "%",
                                "tags": {"hypervisor": hypervisor.id},
                            },
                            {
                                "metric_type": "memory",
                                "metric_name": f"hypervisor_{hypervisor.id}_memory_usage",
                                "value": (
                                    hypervisor.memory_mb_used
                                    / hypervisor.memory_mb
                                    * 100
                                ),
                                "unit": "%",
                                "tags": {"hypervisor": hypervisor.id},
                            },
                        ]
                    )

            elif self.device.subtype == "aws":
                if not self.client:
                    await self.test_connection()

                # 获取EC2实例指标
                cloudwatch = boto3.client(
                    "cloudwatch",
                    aws_access_key_id=self.credentials.get("access_key"),
                    aws_secret_access_key=self.credentials.get("secret_key"),
                    region_name=self.device.config["region"],
                )

                instances = self.client.describe_instances()
                for reservation in instances["Reservations"]:
                    for instance in reservation["Instances"]:
                        instance_id = instance["InstanceId"]

                        # 获取CPU使用率
                        cpu_response = cloudwatch.get_metric_statistics(
                            Namespace="AWS/EC2",
                            MetricName="CPUUtilization",
                            Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
                            StartTime=datetime.utcnow() - timedelta(minutes=5),
                            EndTime=datetime.utcnow(),
                            Period=300,
                            Statistics=["Average"],
                        )

                        if cpu_response["Datapoints"]:
                            metrics.append(
                                {
                                    "metric_type": "cpu",
                                    "metric_name": f"instance_{instance_id}_cpu_usage",
                                    "value": cpu_response["Datapoints"][0]["Average"],
                                    "unit": "%",
                                    "tags": {"instance": instance_id},
                                }
                            )

            return metrics

        except Exception as e:
            logger.error(f"Cloud platform metrics collection failed: {e}")
            return []


# 更新设备处理器映射
def get_device_handler(device: Device) -> BaseDeviceHandler:
    """获取设备处理器"""
    handlers = {
        "network": NetworkDeviceHandler,
        "storage": StorageDeviceHandler,
        "virtualization": VirtualizationHandler,
        "container": ContainerHandler,
        "loadbalancer": LoadBalancerHandler,
        "firewall": FirewallHandler,
        "sdn": SDNControllerHandler,
        "cloud": CloudPlatformHandler,
    }

    handler_class = handlers.get(device.type)
    if not handler_class:
        raise ValueError(f"Unsupported device type: {device.type}")

    return handler_class(device)
