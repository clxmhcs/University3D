# Unity Stage A setup

1. In Unity Hub create a new **URP / Universal 3D** project.
2. Use the repository `UnityProject/` directory as the project location.
3. Install/enable Addressables through Package Manager if the chosen URP template does not already include it.
4. Copy/retain the supplied `Assets/_Project`, `Assets/Art`, `Assets/Scenes`, `Assets/Addressables`, `Assets/Shaders`, and `Assets/ThirdParty` folders.
5. In Unity select:
   `JCU > Stage A > Create Bootstrap Scene`
6. Open `Assets/Scenes/Bootstrap.unity`.
7. Confirm the hierarchy contains:
   - PersistentSystems
   - CampusBridge
   - StageA_DirectionalLight
   - StageA_Camera
   - TEST-01
8. Switch Build Target to iOS and export an iOS build.
9. Embed the exported UnityFramework into the SwiftUI host app.

Do not place real campus buildings in the Bootstrap scene.
