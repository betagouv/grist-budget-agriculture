

```bash
pyenv virtualenv 3.11.9 masaf
pyenv activate masaf
pip install --requirement requirements.txt
pre-commit install
cp .env.local .env
flask --app app run --host=0.0.0.0 --debug
```
