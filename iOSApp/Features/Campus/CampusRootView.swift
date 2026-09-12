import SwiftUI

struct CampusRootView: View {
    @EnvironmentObject private var environment: AppEnvironment
    @State private var lastBridgeEvent = "Bridge idle"

    var body: some View {
        ZStack(alignment: .top) {
            UnityContainer()
                .ignoresSafeArea()

            VStack(spacing: 10) {
                HStack {
                    Text("江城大学 · Stage A")
                        .font(.headline)
                    Spacer()
                    Button("Bridge Test") {
                        environment.bridge.focusObject("TEST-01")
                    }
                }

                Text(lastBridgeEvent)
                    .font(.caption)
                    .frame(maxWidth: .infinity, alignment: .leading)
            }
            .padding()
            .background(.ultraThinMaterial)
        }
        .task {
            environment.bridge.onEvent = { event in
                await MainActor.run {
                    lastBridgeEvent = "\(event.type): \(event.objectID ?? "-")"
                }
            }
        }
    }
}
