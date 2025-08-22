# Tessera

## How to initialize?

```bash
poetry run jam
```

## How to create a conformance target file

```bash
poetry run pyinstaller --clean --onefile --name jam_conformance_target scripts/conformance_target.py   --paths .   --collect-all jam   --collect-all tsrkit_types
```
