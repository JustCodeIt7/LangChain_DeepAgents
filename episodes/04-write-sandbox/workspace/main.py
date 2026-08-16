from fastapi import FastAPI

app = FastAPI()

@app.get("/hello")
async def hello():
    return {"msg": "hello"}
