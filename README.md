# MonitorAPI

A FastAPI-based application for monitoring purposes.

---

## Setup Python Environment

1. Create a virtual environment:
   ```bash
   python -m venv myenv
   ```

2. Activate the virtual environment:
   - On Windows:
     ```bash
     myenv\Scripts\activate
     ```
   - On Linux/MacOS:
     ```bash
     source myenv/bin/activate
     ```

## Install Requirements

```bash
pip install -r requirements.txt
```

## Run the Application

```bash
uvicorn main:app --reload
```
Custom port
```bash
uvicorn main:app --host 0.0.0.0 --port 5001 --reload
```

## Other Commands

- Upgrade pip:
  ```bash
  python.exe -m pip install --upgrade pip
  ```

- Install FastAPI:
  ```bash
  pip install fastapi
  ```

- Install Uvicorn:
  ```bash
  pip install uvicorn
  ```

- Freeze requirements:
  ```bash
  pip freeze > requirements.txt
  ```
- Expose port
  ```bash
  sudo firewall-cmd --zone=public --add-port=5000/tcp --permanent
  sudo firewall-cmd --reload
  ```
