import SwiftUI
import UIKit

struct UnityContainer: View {
    var body: some View {
        UnityContainerRepresentable()
            .background(Color.black)
    }
}

struct UnityContainerRepresentable: UIViewControllerRepresentable {
    func makeUIViewController(context: Context) -> UIViewController {
        UnityBridge.shared.start()

        if let unityViewController = UnityBridge.shared.viewController() {
            return unityViewController
        }

        let placeholder = UIViewController()
        placeholder.view.backgroundColor = .black

        let label = UILabel()
        label.translatesAutoresizingMaskIntoConstraints = false
        label.textColor = .white
        label.numberOfLines = 0
        label.textAlignment = .center
        label.text = "Unity Stage A1\nUnityFramework 尚未嵌入"
        placeholder.view.addSubview(label)

        NSLayoutConstraint.activate([
            label.centerXAnchor.constraint(equalTo: placeholder.view.centerXAnchor),
            label.centerYAnchor.constraint(equalTo: placeholder.view.centerYAnchor)
        ])
        return placeholder
    }

    func updateUIViewController(_ uiViewController: UIViewController, context: Context) {}
}
