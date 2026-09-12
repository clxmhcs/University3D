import SwiftUI

struct UnityContainer: View {
    var body: some View {
        #if canImport(UnityFramework)
        UnityContainerRepresentable()
        #else
        ZStack {
            Rectangle().fill(.black)
            VStack(spacing: 8) {
                Text("Unity Stage A")
                    .foregroundStyle(.white)
                    .font(.title2.bold())
                Text("Attach exported UnityFramework to replace this placeholder.")
                    .foregroundStyle(.secondary)
                    .font(.caption)
            }
        }
        #endif
    }
}

#if canImport(UnityFramework)
import UIKit

struct UnityContainerRepresentable: UIViewControllerRepresentable {
    func makeUIViewController(context: Context) -> UIViewController {
        // Stage A shell only.
        // The actual UnityFramework root view controller is attached
        // after the first Unity iOS export.
        let controller = UIViewController()
        controller.view.backgroundColor = .black
        return controller
    }

    func updateUIViewController(_ uiViewController: UIViewController, context: Context) {}
}
#endif
