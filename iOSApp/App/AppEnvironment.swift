import Foundation

@MainActor
final class AppEnvironment: ObservableObject {
    let bridge = CampusBridge.shared
}
