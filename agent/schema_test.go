package main

import (
	"encoding/json"
	"os"
	"testing"
)

type customSchema struct {
	Properties map[string]struct {
		Enum []string `json:"enum"`
	} `json:"properties"`
}

func TestCustomSchemasMatchRegistrations(t *testing.T) {
	actions := loadCustomSchema(t, "../deps/tools/custom.action.schema.json")
	recognitions := loadCustomSchema(t, "../deps/tools/custom.recognition.schema.json")

	wantActions := make([]string, 0, len(customActions))
	for _, registration := range customActions {
		wantActions = append(wantActions, registration.name)
	}
	assertSameNames(t, "actions", actions.Properties["custom_action"].Enum, wantActions)

	wantRecognitions := make([]string, 0, len(customRecognitions))
	for _, registration := range customRecognitions {
		wantRecognitions = append(wantRecognitions, registration.name)
	}
	assertSameNames(t, "recognitions", recognitions.Properties["custom_recognition"].Enum, wantRecognitions)
}

func loadCustomSchema(t *testing.T, path string) customSchema {
	t.Helper()
	data, err := os.ReadFile(path)
	if err != nil {
		t.Fatalf("read %s: %v", path, err)
	}
	var schema customSchema
	if err := json.Unmarshal(data, &schema); err != nil {
		t.Fatalf("parse %s: %v", path, err)
	}
	return schema
}

func assertSameNames(t *testing.T, kind string, got, want []string) {
	t.Helper()
	gotSet := make(map[string]bool, len(got))
	for _, name := range got {
		if name == "" || gotSet[name] {
			t.Fatalf("schema contains invalid or duplicate %s name %q", kind, name)
		}
		gotSet[name] = true
	}
	for _, name := range want {
		if !gotSet[name] {
			t.Errorf("registered %s %q is missing from schema", kind, name)
		}
	}
	if len(gotSet) != len(want) {
		t.Errorf("schema contains %d %s; registered %d", len(gotSet), kind, len(want))
	}
}
