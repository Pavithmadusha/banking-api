```
python -m venv virtual
virtual\scripts\activate
pip install .\dlib-19.22.99-cp310-cp310-win_amd64.whl
pip install -r requirements.txt
fastapi dev main.py
```
```
CREATE TABLE faces (
    id INT AUTO_INCREMENT PRIMARY KEY,
    userId INT,
    encoding BLOB NOT NULL
);

```