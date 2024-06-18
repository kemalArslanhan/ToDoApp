document.addEventListener("DOMContentLoaded", function() {
    loadTasks();
});

function loadTasks() {
    fetch('/tasks')
        .then(response => response.json())
        .then(data => {
            const taskList = document.getElementById('taskList');
            taskList.innerHTML = '';
            data.forEach((task, index) => {
                const li = document.createElement('li');
                li.textContent = task;
                li.appendChild(createDeleteButton(index));
                taskList.appendChild(li);
            });
        });
}

function addTask() {
    const taskInput = document.getElementById('taskInput');
    const task = taskInput.value;
    fetch('/tasks', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ task: task })
    }).then(response => {
        if (response.ok) {
            loadTasks();
            taskInput.value = '';
        }
    });
}

function deleteTask(taskId) {
    fetch(`/tasks/${taskId}`, {
        method: 'DELETE'
    }).then(response => {
        if (response.ok) {
            loadTasks();
        }
    });
}

function createDeleteButton(taskId) {
    const button = document.createElement('button');
    button.textContent = 'Sil';
    button.onclick = () => deleteTask(taskId);
    return button;
}