from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

app = FastAPI()

class DivideInput(BaseModel):
    a: int
    b: int

@app.post("/divide")
def divide(data: DivideInput):
    # This will raise ZeroDivisionError if b is 0
    return {"result": data.a // data.b}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
