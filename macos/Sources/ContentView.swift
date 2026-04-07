import SwiftUI

// MARK: - Type Badge

private struct TypeBadge: View {
    let type: String

    private var color: Color {
        switch type.lowercased() {
        case "task":  return .green
        case "note":  return .blue
        case "inbox": return .pink
        default:      return .secondary
        }
    }

    var body: some View {
        Text(type.uppercased())
            .font(.system(size: 9, weight: .bold, design: .rounded))
            .foregroundStyle(.white)
            .padding(.horizontal, 6)
            .padding(.vertical, 2)
            .background(color, in: Capsule())
    }
}

// MARK: - Result Card

private struct ResultCard: View {
    let result: ProcessResponse

    var body: some View {
        GroupBox {
            VStack(alignment: .leading, spacing: 10) {
                if result.duplicate {
                    Label("Já existe no Notion", systemImage: "exclamationmark.triangle")
                        .font(.subheadline.weight(.medium))
                        .foregroundStyle(.orange)

                    if let existing = result.existing {
                        Text(existing)
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                } else {
                    HStack(spacing: 6) {
                        if let type = result.type { TypeBadge(type: type) }
                        if let priority = result.priority {
                            Text(priority.uppercased())
                                .font(.system(size: 9, weight: .medium, design: .monospaced))
                                .foregroundStyle(.secondary)
                        }
                    }
                    if let title = result.title {
                        Text(title)
                            .font(.subheadline.weight(.semibold))
                            .foregroundStyle(.primary)
                    }
                }

                if let urlString = result.notionUrl, let url = URL(string: urlString) {
                    Link(destination: url) {
                        Label("Abrir no Notion", systemImage: "arrow.up.right.square")
                            .font(.caption)
                    }
                }

                if let message = result.message, !message.isEmpty {
                    Text(message)
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
        }
        .transition(.move(edge: .bottom).combined(with: .opacity))
    }
}

// MARK: - Content View

struct ContentView: View {
    @State private var message = ""
    @State private var isLoading = false
    @State private var result: ProcessResponse?
    @State private var errorText: String?
    @FocusState private var inputFocused: Bool

    private var canSend: Bool {
        !message.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty && !isLoading
    }

    var body: some View {
        VStack(alignment: .leading, spacing: 14) {
            Label("Personal Assistant", systemImage: "brain")
                .font(.headline)
                .foregroundStyle(.primary)

            TextField("Task, nota ou mensagem...", text: $message, axis: .vertical)
                .lineLimit(3...7)
                .textFieldStyle(.plain)
                .padding(10)
                .background(.quinary, in: RoundedRectangle(cornerRadius: 8))
                .focused($inputFocused)
                .onSubmit(submit)

            HStack {
                Text("Return para enviar · Shift+Return para nova linha")
                    .font(.caption2)
                    .foregroundStyle(.tertiary)
                Spacer()
                Button(action: submit) {
                    if isLoading {
                        ProgressView().scaleEffect(0.75)
                            .frame(width: 16, height: 16)
                    } else {
                        Text("Enviar")
                    }
                }
                .buttonStyle(.borderedProminent)
                .disabled(!canSend)
            }

            if let result {
                ResultCard(result: result)
            }

            if let errorText {
                Label(errorText, systemImage: "exclamationmark.circle")
                    .font(.caption)
                    .foregroundStyle(.red)
            }
        }
        .padding(16)
        .frame(width: 340)
        .onAppear { inputFocused = true }
    }

    private func submit() {
        let trimmed = message.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmed.isEmpty else { return }

        isLoading = true
        errorText = nil
        result = nil

        Task {
            do {
                let response = try await APIService.shared.process(message: trimmed)
                await MainActor.run {
                    withAnimation(.easeOut(duration: 0.2)) {
                        self.result = response
                        self.message = ""
                    }
                    self.isLoading = false
                }
            } catch {
                await MainActor.run {
                    self.errorText = error.localizedDescription
                    self.isLoading = false
                }
            }
        }
    }
}
