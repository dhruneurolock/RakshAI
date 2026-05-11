# Goal Description

To enable true end-to-end LLM-driven scanning, we must implement the Docker Option. The security tools (`httpx`, `sqlmap`, `nuclei`, `katana`, etc.) required by the LLM pipeline are Linux-based and hardcoded to execute at `/usr/local/bin/...` natively by the `tool_sandbox.py`. 

This plan will containerize **only your Python backend**, equipping it with all necessary cybersecurity tools, while leaving your databases (Postgres, Redis, Neo4j) and Ollama running natively on your Windows D: drive. The container will securely communicate back into your Windows host to utilize Ollama.

## User Review Required

> [!WARNING]
> Building this Docker image will take several minutes the first time because we are compiling and downloading penetration testing tools like `Go`, `httpx`, `nuclei`, and `sqlmap` directly into the container. 
> 
> You **must** have Docker Desktop installed and running on your Windows machine (configured to allow access to the D: drive if prompted).

## Proposed Changes

---

### Docker Infrastructure

I will create the necessary Docker configuration to run the backend and install the tools.

#### [NEW] `backend/Dockerfile`
A Debian-based Python image that installs:
- Core networking tools.
- Golang (required to build ProjectDiscovery tools).
- Security binaries (`httpx`, `katana`, `nuclei`, `subfinder`, `dalfox`, `sqlmap`).
- Python requirements (`requirements.txt`).

#### [NEW] `docker-compose.yml` (in the root directory)
A `docker-compose` setup specifically designed for Windows Local Development:
- Service: `backend`.
- **CRITICAL:** Replaces all `.env` `localhost` references with `host.docker.internal` so the container can escape out and talk to your native Windows Ollama, Postgres, Neo4j, and Redis ports without you needing to containerize them.
- Mounts the `D:\NeuroPentWeb\backend` folder live so you can still edit code natively.

---

### Custom Tool Stubs

The code in `tool_sandbox.py` references two custom python tools that currently do not exist in your directory.

#### [NEW] `backend/app/tools/custom/idor_tester.py`
A python script simulating an IDOR vulnerability test (used by the ExploitExecutionAgent).

#### [NEW] `backend/app/tools/custom/auth_bypass.py`
A python script simulating an authentication bypass test. 

## Open Questions

> [!IMPORTANT]
> 1. Do you have **Docker Desktop** currently open and running in your Windows taskbar right now?
> 2. Are you perfectly fine keeping Postgres, Neo4j, Redis, and Ollama running natively outside of Docker using your `start-local.ps1` script, and just running the backend itself in Docker?

## Verification Plan

### Automated Tests
- I will run `docker-compose up --build -d` to compile the image.
- We will verify that the container successfully boots on port `8000`.

### Manual Verification
- You will initiate a scan via the frontend UI (`http://localhost:5173`).
- We will monitor the Docker container logs to verify `httpx` and `katana` are successfully launching via the `ToolSandbox` without crashing.
