
# Unboxd API
Unboxd is the backend API for a web extension called **Unboxd**. It provides the necessary endpoints to support the extension’s functionality.

### Project Structure
- Backend Repository: **You are here**
- WebExtension Repository: *Not public yet*
- Hackathon Repository: Holds the prototype code. [Github Link](https://github.com/nisooom/generics)


## Tech Stack
- Python
- FastAPI with uvicorn server
- Models are built with Pytorch


## Geting Sstarted

1. Clone the repository
2. Create a new virtual environment (optional but recommended, pls do it)
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```
3. Install dependency
```bash
pip install -r requirements.txt
```
4. Install pytorch, this is not included in requirments.txt to provide customization. See more on: [Pytorch Installation](https://docs.pytorch.org/get-started/locally)
```bash
# for cpu only
pip install torch --index-url https://download.pytorch.org/whl/cpu
# for cuda enabled
pip install torch --index-url https://download.pytorch.org/whl/cu128
```
5. Starting the server
```bash
# development mode
uvicorn main:app --reload
# production mode
uvicorn main:app --host 0.0.0.0
```

## Docker support
- Repository provides a docker file which inherits from **python:3.12-slim** to have small image footprint
- The image only downloads the **CPU-Only** version of pytorch
```bash
docker build -t unboxd-api -f docker/Dockerfile .
```
