if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api.routes:app", host="127.0.0.1", port=4000, reload=True)
