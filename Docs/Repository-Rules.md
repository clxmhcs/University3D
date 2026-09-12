# Repository rules

- Main repository layout is fixed:
  `iOSApp / UnityProject / CampusData / Tools / Tests / Docs / BuildScripts`.
- Git LFS from day one for large art binaries.
- Never commit:
  `UnityProject/Library`, `UnityProject/Temp`, `UnityProject/Logs`, `DerivedData`, `build`.
- Swift, C#, JSON and documentation stay in normal Git.
- `main` + lightweight `feature/...` branches are sufficient.
- Campus coordinates must flow from CampusData. Do not repair layout by dragging production objects in Unity.
