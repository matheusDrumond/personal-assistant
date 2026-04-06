import SwiftUI

// MARK: - Hex Color Helper

extension Color {
    init(hex: String) {
        let hex = hex.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)
        var int: UInt64 = 0
        Scanner(string: hex).scanHexInt64(&int)
        let a, r, g, b: UInt64
        switch hex.count {
        case 3:  (a, r, g, b) = (255, (int >> 8) * 17, (int >> 4 & 0xF) * 17, (int & 0xF) * 17)
        case 6:  (a, r, g, b) = (255, int >> 16, int >> 8 & 0xFF, int & 0xFF)
        case 8:  (a, r, g, b) = (int >> 24, int >> 16 & 0xFF, int >> 8 & 0xFF, int & 0xFF)
        default: (a, r, g, b) = (255, 0, 0, 0)
        }
        self.init(.sRGB,
                  red: Double(r) / 255,
                  green: Double(g) / 255,
                  blue: Double(b) / 255,
                  opacity: Double(a) / 255)
    }
}

// MARK: - Design Tokens

private enum C {
    static let bg        = Color(hex: "#0a0a0f")
    static let surface   = Color(hex: "#13131a")
    static let border    = Color(hex: "#2a2a3a")
    static let text      = Color(hex: "#e8e8f0")
    static let muted     = Color(hex: "#6b6b7b")
    static let green     = Color(hex: "#7fff6e")
    static let blue      = Color(hex: "#6eb8ff")
    static let pink      = Color(hex: "#ff6eb4")
}

// MARK: - Type Badge

private struct TypeBadge: View {
    let type: String

    private var color: Color {
        switch type.lowercased() {
        case "task":  return C.green
        case "note":  return C.blue
        case "inbox": return C.pink
        default:      return C.muted
        }
    }

    var body: some View {
        Text(type.uppercased())
            .font(.system(size: 10, weight: .bold, design: .monospaced))
            .foregroundColor(.black)
            .padding(.horizontal, 7)
            .padding(.vertical, 3)
            .background(RoundedRectangle(cornerRadius: 4).fill(color))
    }
}

// MARK: - Result Card

private struct ResultCard: View {
    let result: ProcessResponse

    var body: some View {
        VStack(alignment: .leading, spacing: 10) {
            if result.duplicate {
                duplicateContent
            } else {
                newItemContent
            }

            if let urlString = result.notionUrl, let url = URL(string: urlString) {
                Link("Abrir no Notion →", destination: url)
                    .font(.system(size: 12))
                    .foregroundColor(C.green)
            }
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(16)
        .background(
            RoundedRectangle(cornerRadius: 12)
                .fill(C.surface)
                .overlay(RoundedRectangle(cornerRadius: 12).stroke(C.border, lineWidth: 1))
        )
    }

    private var duplicateContent: some View {
        VStack(alignment: .leading, spacing: 6) {
            HStack(spacing: 6) {
                Image(systemName: "exclamationmark.triangle.fill")
                    .foregroundColor(.yellow)
                Text("Já existe")
                    .fontWeight(.semibold)
                    .foregroundColor(.yellow)
            }
            if let existing = result.existing {
                Text(existing)
                    .font(.system(size: 12))
                    .foregroundColor(C.muted)
            }
        }
    }

    private var newItemContent: some View {
        VStack(alignment: .leading, spacing: 8) {
            HStack(spacing: 8) {
                if let type = result.type {
                    TypeBadge(type: type)
                }
                if let priority = result.priority {
                    Text(priority.uppercased())
                        .font(.system(size: 10, weight: .medium, design: .monospaced))
                        .foregroundColor(C.muted)
                }
            }
            if let title = result.title {
                Text(title)
                    .font(.headline)
                    .foregroundColor(C.text)
            }
        }
    }
}

// MARK: - Main View

struct ContentView: View {
    @State private var message = ""
    @State private var isLoading = false
    @State private var result: ProcessResponse?
    @State private var errorText: String?
    @FocusState private var inputFocused: Bool

    private var canSend: Bool { !message.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty && !isLoading }

    var body: some View {
        C.bg.ignoresSafeArea()
            .overlay {
                VStack(alignment: .center, spacing: 24) {
                    header
                    inputSection
                    if let result { ResultCard(result: result).transition(.move(edge: .bottom).combined(with: .opacity)) }
                    if let errorText { errorBanner(errorText) }
                    Spacer(minLength: 0)
                }
                .padding(32)
                .frame(maxWidth: 640)
            }
            .frame(minWidth: 500, idealWidth: 640, minHeight: 420)
            .onAppear { inputFocused = true }
    }

    // MARK: Subviews

    private var header: some View {
        VStack(spacing: 4) {
            Text("Personal Assistant")
                .font(.title2.weight(.semibold))
                .foregroundColor(C.text)
            Text("Tasks, notas e inbox — tudo no Notion")
                .font(.caption)
                .foregroundColor(C.muted)
        }
    }

    private var inputSection: some View {
        VStack(alignment: .trailing, spacing: 10) {
            TextField("Adicione uma task, nota ou mensagem para o inbox...", text: $message, axis: .vertical)
                .font(.body)
                .foregroundColor(C.text)
                .lineLimit(4...8)
                .focused($inputFocused)
                .textFieldStyle(.plain)
                .padding(12)
                .background(
                    RoundedRectangle(cornerRadius: 12)
                        .fill(C.surface)
                        .overlay(RoundedRectangle(cornerRadius: 12).stroke(C.border, lineWidth: 1))
                )

            Button(action: submit) {
                HStack(spacing: 6) {
                    if isLoading {
                        ProgressView().scaleEffect(0.75).tint(.black)
                    }
                    Text(isLoading ? "Processando..." : "Enviar")
                        .fontWeight(.medium)
                }
                .foregroundColor(.black)
                .padding(.horizontal, 20)
                .padding(.vertical, 8)
                .background(
                    RoundedRectangle(cornerRadius: 8)
                        .fill(canSend ? C.green : C.muted)
                )
            }
            .buttonStyle(.plain)
            .disabled(!canSend)
            .keyboardShortcut(.return, modifiers: .command)
        }
    }

    private func errorBanner(_ text: String) -> some View {
        Text(text)
            .font(.caption)
            .foregroundColor(.red.opacity(0.85))
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(12)
            .background(
                RoundedRectangle(cornerRadius: 8)
                    .fill(Color.red.opacity(0.08))
                    .overlay(RoundedRectangle(cornerRadius: 8).stroke(Color.red.opacity(0.2), lineWidth: 1))
            )
    }

    // MARK: Action

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
                    withAnimation(.easeOut(duration: 0.25)) {
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
