import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import App from "./App";
import { AuthProvider } from "./AuthContext";

describe("App Component", () => {
  it("renders login page by default when unauthenticated", () => {
    // Wrap App in AuthProvider to give it context
    render(
      <AuthProvider>
        <App />
      </AuthProvider>
    );

    // After loading, it should display the "Tech Noir RAG" branding and prompt
    // Wait for the login screen to render
    expect(screen.getByText(/Tech Noir RAG/i)).toBeInTheDocument();
    
    // Auth mode should initially be set to login
    expect(screen.getByText(/Sign in to continue your research/i)).toBeInTheDocument();
  });
});
