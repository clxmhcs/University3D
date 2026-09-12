# iOS Stage A setup

Create a normal SwiftUI iOS app in Xcode, then use the supplied Swift source layout under `iOSApp/`.

The first integration goal is not the finished app UI. It is:

- host SwiftUI screen,
- UnityFramework view,
- CampusBridgeProtocol v1 round-trip.

After the first Unity iOS export is embedded, replace the Stage A placeholder lifecycle in `UnityContainer.swift` with the exported UnityFramework root-view lifecycle. Keep all Unity calls behind `UnityBridge`.

Do not call Unity GameObjects directly from feature ViewModels.
