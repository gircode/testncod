"""
Monitoring Data Exporter Module
"""

import csv
import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import yaml
from prometheus_client.parser import text_string_to_metric_families


class MetricsExporter:
    """Class for exporting monitoring metrics"""

    def __init__(self, output_dir: str):
        """Initialize metrics exporter"""
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def export_metrics(
        self,
        metrics: Dict[str, Any],
        format: str = "json",
        filename: Optional[str] = None,
    ) -> str:
        """Export metrics to file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"metrics_{timestamp}.{format}"

        output_path = os.path.join(self.output_dir, filename)

        if format == "json":
            self._export_json(metrics, output_path)
        elif format == "csv":
            self._export_csv(metrics, output_path)
        elif format == "yaml":
            self._export_yaml(metrics, output_path)
        else:
            raise ValueError(f"Unsupported format: {format}")

        return output_path

    def _export_json(self, metrics: Dict[str, Any], output_path: str):
        """Export metrics to JSON file"""
        with open(output_path, "w") as f:
            json.dump(metrics, f, indent=2)

    def _export_csv(self, metrics: Dict[str, Any], output_path: str):
        """Export metrics to CSV file"""
        # Flatten metrics dictionary
        flattened = self._flatten_dict(metrics)

        # Write to CSV
        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Metric", "Value"])
            for key, value in flattened.items():
                writer.writerow([key, value])

    def _export_yaml(self, metrics: Dict[str, Any], output_path: str):
        """Export metrics to YAML file"""
        with open(output_path, "w") as f:
            yaml.dump(metrics, f, default_flow_style=False)

    def _flatten_dict(
        self, d: Dict[str, Any], parent_key: str = "", sep: str = "."
    ) -> Dict[str, Any]:
        """Flatten nested dictionary"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep).items())
            else:
                items.append((new_key, v))
        return dict(items)


class MetricsVisualizer:
    """Class for creating visualizations of monitoring metrics"""

    def __init__(self, output_dir: str):
        """Initialize metrics visualizer"""
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        # Set up plotting style
        plt.style.use("seaborn")
        sns.set_palette("husl")

    def create_time_series_plot(
        self,
        data: Dict[str, List[Dict[str, Union[str, float]]]],
        metric_name: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        filename: Optional[str] = None,
    ) -> str:
        """Create time series plot for metric"""
        # Convert data to DataFrame
        df = pd.DataFrame(data[metric_name])
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df.set_index("timestamp", inplace=True)

        # Apply time range filter if specified
        if start_time:
            df = df[df.index >= start_time]
        if end_time:
            df = df[df.index <= end_time]

        # Create plot
        plt.figure(figsize=(12, 6))
        plt.plot(df.index, df["value"])
        plt.title(f"{metric_name} Over Time")
        plt.xlabel("Time")
        plt.ylabel("Value")
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Save plot
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{metric_name}_{timestamp}.png"

        output_path = os.path.join(self.output_dir, filename)
        plt.savefig(output_path)
        plt.close()

        return output_path

    def create_histogram(
        self,
        data: List[float],
        metric_name: str,
        bins: int = 50,
        filename: Optional[str] = None,
    ) -> str:
        """Create histogram for metric values"""
        plt.figure(figsize=(10, 6))
        plt.hist(data, bins=bins, edgecolor="black")
        plt.title(f"Distribution of {metric_name}")
        plt.xlabel("Value")
        plt.ylabel("Frequency")
        plt.grid(True)
        plt.tight_layout()

        # Save plot
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{metric_name}_hist_{timestamp}.png"

        output_path = os.path.join(self.output_dir, filename)
        plt.savefig(output_path)
        plt.close()

        return output_path

    def create_box_plot(
        self,
        data: Dict[str, List[float]],
        metric_name: str,
        filename: Optional[str] = None,
    ) -> str:
        """Create box plot for metric values by category"""
        plt.figure(figsize=(10, 6))
        plt.boxplot(data.values(), labels=data.keys())
        plt.title(f"Distribution of {metric_name} by Category")
        plt.xlabel("Category")
        plt.ylabel("Value")
        plt.grid(True)
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Save plot
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{metric_name}_box_{timestamp}.png"

        output_path = os.path.join(self.output_dir, filename)
        plt.savefig(output_path)
        plt.close()

        return output_path

    def create_heatmap(
        self, data: pd.DataFrame, metric_name: str, filename: Optional[str] = None
    ) -> str:
        """Create heatmap for metric correlations"""
        plt.figure(figsize=(10, 8))
        sns.heatmap(data.corr(), annot=True, cmap="coolwarm", center=0, fmt=".2f")
        plt.title(f"Correlation Heatmap - {metric_name}")
        plt.tight_layout()

        # Save plot
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{metric_name}_heatmap_{timestamp}.png"

        output_path = os.path.join(self.output_dir, filename)
        plt.savefig(output_path)
        plt.close()

        return output_path


class PrometheusExporter:
    """Class for exporting Prometheus metrics"""

    def __init__(self, output_dir: str):
        """Initialize Prometheus exporter"""
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def export_metrics(
        self, metrics_text: str, format: str = "json", filename: Optional[str] = None
    ) -> str:
        """Export Prometheus metrics to file"""
        # Parse metrics
        metrics = {}
        for family in text_string_to_metric_families(metrics_text):
            family_name = family.name
            metrics[family_name] = []

            for sample in family.samples:
                sample_data = {
                    "name": sample.name,
                    "labels": sample.labels,
                    "value": sample.value,
                    "timestamp": datetime.now().isoformat(),
                }
                metrics[family_name].append(sample_data)

        # Export metrics
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"prometheus_metrics_{timestamp}.{format}"

        output_path = os.path.join(self.output_dir, filename)

        if format == "json":
            with open(output_path, "w") as f:
                json.dump(metrics, f, indent=2)
        elif format == "yaml":
            with open(output_path, "w") as f:
                yaml.dump(metrics, f, default_flow_style=False)
        else:
            raise ValueError(f"Unsupported format: {format}")

        return output_path

    def create_snapshot(
        self, metrics_text: str, snapshot_dir: Optional[str] = None
    ) -> str:
        """Create a snapshot of current metrics"""
        if not snapshot_dir:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            snapshot_dir = os.path.join(self.output_dir, f"snapshot_{timestamp}")

        os.makedirs(snapshot_dir, exist_ok=True)

        # Export metrics in different formats
        self.export_metrics(metrics_text, format="json", filename="metrics.json")
        self.export_metrics(metrics_text, format="yaml", filename="metrics.yaml")

        # Create README with snapshot info
        readme_path = os.path.join(snapshot_dir, "README.md")
        with open(readme_path, "w") as f:
            f.write(f"# Metrics Snapshot\n\n")
            f.write(f"Created at: {datetime.now().isoformat()}\n\n")
            f.write("## Contents\n\n")
            f.write("- `metrics.json`: Metrics in JSON format\n")
            f.write("- `metrics.yaml`: Metrics in YAML format\n")

        return snapshot_dir
