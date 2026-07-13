package main

import "testing"

func TestAgentIdentifier(t *testing.T) {
	id, err := agentIdentifier([]string{"agent.exe", "generated-socket-id"})
	if err != nil {
		t.Fatalf("agentIdentifier() error = %v", err)
	}
	if id != "generated-socket-id" {
		t.Fatalf("agentIdentifier() = %q", id)
	}
}

func TestAgentIdentifierRequiresClientValue(t *testing.T) {
	if _, err := agentIdentifier([]string{"agent.exe"}); err == nil {
		t.Fatal("agentIdentifier() error = nil, want missing identifier error")
	}
}
