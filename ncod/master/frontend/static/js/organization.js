// 部门管理
function addDepartment() {
    document.getElementById('departmentForm').reset();
    document.getElementById('departmentDialog').style.display = 'block';
}

function editDepartment(deptId) {
    fetch(`/api/departments/${deptId}`)
        .then(response => response.json())
        .then(dept => {
            document.getElementById('deptName').value = dept.name;
            document.getElementById('parentDept').value = dept.parent_id || '';
            document.getElementById('departmentForm').dataset.id = deptId;
            document.getElementById('departmentDialog').style.display = 'block';
        })
        .catch(error => console.error('Error fetching department:', error));
}

function deleteDepartment(deptId) {
    if (!confirm('确定要删除此部门吗？')) return;

    fetch(`/api/departments/${deptId}`, {
        method: 'DELETE'
    })
        .then(response => response.json())
        .then(() => {
            location.reload();
        })
        .catch(error => console.error('Error deleting department:', error));
}

function closeDepartmentDialog() {
    document.getElementById('departmentDialog').style.display = 'none';
}

// 管线管理
function addPipeline() {
    document.getElementById('pipelineForm').reset();
    document.getElementById('nodeList').innerHTML = '';
    document.getElementById('pipelineDialog').style.display = 'block';
}

function editPipeline(pipelineId) {
    fetch(`/api/pipelines/${pipelineId}`)
        .then(response => response.json())
        .then(pipeline => {
            document.getElementById('pipelineName').value = pipeline.name;
            document.getElementById('pipelineDept').value = pipeline.department_id;
            
            // 加载节点配置
            const nodeList = document.getElementById('nodeList');
            nodeList.innerHTML = '';
            pipeline.nodes.forEach(node => {
                addNodeToList(node);
            });
            
            document.getElementById('pipelineForm').dataset.id = pipelineId;
            document.getElementById('pipelineDialog').style.display = 'block';
        })
        .catch(error => console.error('Error fetching pipeline:', error));
}

function deletePipeline(pipelineId) {
    if (!confirm('确定要删除此管线吗？')) return;

    fetch(`/api/pipelines/${pipelineId}`, {
        method: 'DELETE'
    })
        .then(response => response.json())
        .then(() => {
            location.reload();
        })
        .catch(error => console.error('Error deleting pipeline:', error));
}

function closePipelineDialog() {
    document.getElementById('pipelineDialog').style.display = 'none';
}

// 节点管理
function addNode(node = {}) {
    const nodeList = document.getElementById('nodeList');
    const nodeDiv = document.createElement('div');
    nodeDiv.className = 'node-config-item';
    nodeDiv.innerHTML = `
        <select name="node_type[]" required>
            <option value="master" ${node.type === 'master' ? 'selected' : ''}>主节点</option>
            <option value="slave" ${node.type === 'slave' ? 'selected' : ''}>从节点</option>
        </select>
        <input type="text" name="node_address[]" placeholder="节点地址" value="${node.address || ''}" required>
        <button type="button" onclick="removeNode(this)" class="btn-danger btn-small">删除</button>
    `;
    nodeList.appendChild(nodeDiv);
}

function removeNode(button) {
    button.parentElement.remove();
}

// 表单提交处理
document.getElementById('departmentForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData.entries());
    const deptId = e.target.dataset.id;
    
    try {
        const response = await fetch(`/api/departments${deptId ? `/${deptId}` : ''}`, {
            method: deptId ? 'PUT' : 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            location.reload();
        } else {
            alert('保存失败');
        }
    } catch (error) {
        console.error('Error saving department:', error);
        alert('保存失败');
    }
});

document.getElementById('pipelineForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const pipelineId = e.target.dataset.id;
    
    // 收集节点配置
    const nodes = [];
    const types = formData.getAll('node_type[]');
    const addresses = formData.getAll('node_address[]');
    
    for (let i = 0; i < types.length; i++) {
        nodes.push({
            type: types[i],
            address: addresses[i]
        });
    }
    
    const data = {
        name: formData.get('name'),
        department_id: formData.get('department_id'),
        nodes: nodes
    };
    
    try {
        const response = await fetch(`/api/pipelines${pipelineId ? `/${pipelineId}` : ''}`, {
            method: pipelineId ? 'PUT' : 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            location.reload();
        } else {
            alert('保存失败');
        }
    } catch (error) {
        console.error('Error saving pipeline:', error);
        alert('保存失败');
    }
}); 