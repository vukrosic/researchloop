import SwiftUI
import AppKit

@main
struct HeatLensApp: App {
    @StateObject private var monitor = HeatMonitor()

    var body: some Scene {
        WindowGroup("Heat Lens") {
            ContentView(monitor: monitor)
                .frame(minWidth: 760, minHeight: 560)
        }
        .windowResizability(.contentMinSize)
    }
}

@MainActor
final class HeatMonitor: ObservableObject {
    @Published var snapshot = HeatSnapshot.empty

    private var refreshLoop: Task<Void, Never>?

    init() {
        refresh()
        refreshLoop = Task { [weak self] in
            while !Task.isCancelled {
                try? await Task.sleep(for: .seconds(2))
                await MainActor.run {
                    self?.refresh()
                }
            }
        }
    }

    deinit {
        refreshLoop?.cancel()
    }

    func refresh() {
        snapshot = HeatSnapshot.capture(limit: 12)
    }

    func terminate(pid: Int) {
        Task.detached(priority: .userInitiated) {
            let task = Process()
            task.executableURL = URL(fileURLWithPath: "/bin/kill")
            task.arguments = ["-TERM", String(pid)]

            do {
                try task.run()
                task.waitUntilExit()
            } catch {
                return
            }

            await MainActor.run {
                self.refresh()
            }
        }
    }
}

struct HeatSnapshot {
    let updatedAt: Date
    let thermalState: ThermalState
    let processes: [ProcessSample]

    static let empty = HeatSnapshot(
        updatedAt: .now,
        thermalState: .nominal,
        processes: []
    )

    static func capture(limit: Int) -> HeatSnapshot {
        HeatSnapshot(
            updatedAt: .now,
            thermalState: ThermalState(processInfo: ProcessInfo.processInfo.thermalState),
            processes: ProcessSampler.topProcesses(limit: limit)
        )
    }
}

struct ProcessSample: Identifiable {
    let pid: Int
    let ppid: Int
    let cpu: Double
    let memory: Double
    let command: String

    var id: Int { pid }

    var name: String {
        let firstToken = command.split(separator: " ", maxSplits: 1, omittingEmptySubsequences: true).first ?? ""
        guard !firstToken.isEmpty else { return command }
        let path = String(firstToken)
        return URL(fileURLWithPath: path).lastPathComponent.isEmpty ? path : URL(fileURLWithPath: path).lastPathComponent
    }

    var detail: String {
        let trimmed = command.trimmingCharacters(in: .whitespacesAndNewlines)
        if trimmed == name {
            return trimmed
        }
        return trimmed.replacingOccurrences(of: name, with: "", options: [.anchored], range: trimmed.startIndex..<trimmed.endIndex).trimmingCharacters(in: .whitespaces)
    }

    var heatHint: String {
        if cpu >= 30 {
            return "likely heat source"
        }
        if cpu >= 10 {
            return "active background load"
        }
        if memory >= 3 {
            return "memory-heavy"
        }
        return "light activity"
    }
}

enum ThermalState: String {
    case nominal
    case fair
    case serious
    case critical
    case unknown

    init(processInfo: ProcessInfo.ThermalState) {
        switch processInfo {
        case .nominal:
            self = .nominal
        case .fair:
            self = .fair
        case .serious:
            self = .serious
        case .critical:
            self = .critical
        @unknown default:
            self = .unknown
        }
    }

    var label: String {
        switch self {
        case .nominal: return "Nominal"
        case .fair: return "Warm"
        case .serious: return "Hot"
        case .critical: return "Critical"
        case .unknown: return "Unknown"
        }
    }

    var subtitle: String {
        switch self {
        case .nominal: return "The Mac is comfortably within normal thermal limits."
        case .fair: return "Fan pressure or load is starting to build."
        case .serious: return "The Mac is under sustained heat pressure."
        case .critical: return "macOS is trying hard to cool things down."
        case .unknown: return "macOS did not report a thermal state."
        }
    }

    var color: Color {
        switch self {
        case .nominal: return .green
        case .fair: return .yellow
        case .serious: return .orange
        case .critical: return .red
        case .unknown: return .secondary
        }
    }

    var symbolName: String {
        switch self {
        case .nominal: return "thermometer.low"
        case .fair: return "thermometer.medium"
        case .serious: return "thermometer.high"
        case .critical: return "flame.fill"
        case .unknown: return "questionmark.circle"
        }
    }
}

enum ProcessSampler {
    static func topProcesses(limit: Int) -> [ProcessSample] {
        let command = """
        ps -Ao pid=,ppid=,%cpu=,%mem=,command= | sort -k3 -nr | head -n \(limit)
        """

        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/bin/sh")
        process.arguments = ["-c", command]

        let pipe = Pipe()
        process.standardOutput = pipe
        process.standardError = Pipe()

        do {
            try process.run()
            process.waitUntilExit()
        } catch {
            return []
        }

        let data = pipe.fileHandleForReading.readDataToEndOfFile()
        let output = String(decoding: data, as: UTF8.self)
        return output
            .split(whereSeparator: \.isNewline)
            .compactMap(parseLine)
    }

    private static func parseLine(_ line: Substring) -> ProcessSample? {
        let trimmed = line.trimmingCharacters(in: .whitespaces)
        guard !trimmed.isEmpty else { return nil }

        let fields = trimmed.split(maxSplits: 4, omittingEmptySubsequences: true, whereSeparator: { $0.isWhitespace })
        guard fields.count == 5,
              let pid = Int(fields[0]),
              let ppid = Int(fields[1]),
              let cpu = Double(fields[2]),
              let memory = Double(fields[3]) else {
            return nil
        }

        return ProcessSample(
            pid: pid,
            ppid: ppid,
            cpu: cpu,
            memory: memory,
            command: String(fields[4])
        )
    }
}

struct ContentView: View {
    @ObservedObject var monitor: HeatMonitor

    var body: some View {
        let snapshot = monitor.snapshot

        ScrollView(.vertical) {
            VStack(alignment: .leading, spacing: 18) {
                header(snapshot: snapshot)

                HStack(alignment: .top, spacing: 16) {
                    thermalCard(snapshot: snapshot)
                    processCard(snapshot: snapshot)
                }

                noteCard

                Spacer(minLength: 0)
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
        .padding(20)
        .background(
            LinearGradient(
                colors: [
                    Color(nsColor: .windowBackgroundColor),
                    Color(nsColor: .underPageBackgroundColor)
                ],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
        )
    }

    @ViewBuilder
    private func header(snapshot: HeatSnapshot) -> some View {
        HStack {
            VStack(alignment: .leading, spacing: 6) {
                Text("Heat Lens")
                    .font(.system(size: 30, weight: .bold, design: .rounded))
                Text("See the thermal state and the processes most likely making your Mac hot.")
                    .font(.callout)
                    .foregroundStyle(.secondary)
            }

            Spacer()

            Button("Refresh Now") {
                monitor.refresh()
            }
            .buttonStyle(.borderedProminent)
        }
    }

    @ViewBuilder
    private func thermalCard(snapshot: HeatSnapshot) -> some View {
        VStack(alignment: .leading, spacing: 14) {
            Label {
                Text(snapshot.thermalState.label)
                    .font(.headline)
            } icon: {
                Image(systemName: snapshot.thermalState.symbolName)
            }
            .foregroundStyle(snapshot.thermalState.color)

            Text(snapshot.thermalState.subtitle)
                .font(.body)

            VStack(alignment: .leading, spacing: 6) {
                Text("What this means")
                    .font(.caption)
                    .foregroundStyle(.secondary)
                Text("macOS does not expose a reliable public temperature sensor API. This app uses thermal state plus CPU/memory usage as the best public proxy for what is heating the machine.")
                    .font(.callout)
                    .foregroundStyle(.secondary)
            }

            Text("Updated \(snapshot.updatedAt.formatted(date: .omitted, time: .standard))")
                .font(.caption)
                .foregroundStyle(.secondary)
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(cardBackground)
    }

    @ViewBuilder
    private func processCard(snapshot: HeatSnapshot) -> some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Text("Likely heat sources")
                    .font(.headline)
                Spacer()
                Text("\(snapshot.processes.count) sampled")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }

            if snapshot.processes.isEmpty {
                VStack(alignment: .leading, spacing: 8) {
                    Text("Sampling did not return any processes yet.")
                        .foregroundStyle(.secondary)
                    Text("Press Refresh Now or wait a couple seconds. If this keeps happening, the `ps` sample may be blocked or the command parser needs adjusting.")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            } else {
                LazyVStack(spacing: 10) {
                    ForEach(snapshot.processes) { sample in
                        ProcessRow(sample: sample, maxCPU: snapshot.processes.map(\.cpu).max() ?? 1) {
                            monitor.terminate(pid: sample.pid)
                        }
                    }
                }
            }
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(cardBackground)
    }

    private var noteCard: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("How to use it")
                .font(.headline)
            Text("Open the app, watch the top rows change, and look for a process that stays near the top while the thermal state moves from Nominal to Warm, Hot, or Critical.")
                .foregroundStyle(.secondary)
            Text("Tip: if the hottest process is a browser helper, chat app helper, or Codex/Claude worker, that is usually the real source of the heat, not the window itself.")
                .foregroundStyle(.secondary)
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(cardBackground)
    }

    private var cardBackground: some View {
        RoundedRectangle(cornerRadius: 18, style: .continuous)
            .fill(Color(nsColor: .controlBackgroundColor))
            .shadow(color: .black.opacity(0.08), radius: 12, x: 0, y: 6)
    }
}

struct ProcessRow: View {
    let sample: ProcessSample
    let maxCPU: Double
    let terminate: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(alignment: .firstTextBaseline) {
                VStack(alignment: .leading, spacing: 2) {
                    Text(sample.name)
                        .font(.system(.body, design: .rounded))
                        .fontWeight(.semibold)
                    Text("PID \(sample.pid)  •  \(sample.heatHint)")
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }

                Spacer()

                VStack(alignment: .trailing, spacing: 2) {
                    Text(String(format: "%.1f%% CPU", sample.cpu))
                        .font(.system(.body, design: .monospaced))
                    Text(String(format: "%.1f%% MEM", sample.memory))
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }

            HStack {
                Spacer()
                Button("Terminate") {
                    terminate()
                }
                .buttonStyle(.bordered)
                .tint(.red)
            }

            ProgressView(value: min(sample.cpu / max(maxCPU, 1), 1.0))
                .tint(barColor)

            if sample.detail.isEmpty == false {
                Text(sample.detail)
                    .font(.caption2)
                    .foregroundStyle(.secondary)
                    .lineLimit(1)
            }
        }
        .padding(12)
        .background(
            RoundedRectangle(cornerRadius: 14, style: .continuous)
                .fill(Color(nsColor: .windowBackgroundColor).opacity(0.75))
        )
    }

    private var barColor: Color {
        switch sample.cpu {
        case 30...: return .red
        case 10..<30: return .orange
        case 3..<10: return .yellow
        default: return .green
        }
    }
}
