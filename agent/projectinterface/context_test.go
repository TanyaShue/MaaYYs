package projectinterface

import "testing"

func TestLoad(t *testing.T) {
	t.Setenv(EnvInterfaceVersion, "v2.8.1")
	t.Setenv(EnvClientName, "MXU")
	t.Setenv(EnvController, `{"name":"Android","label":"安卓设备","type":"Adb"}`)
	t.Setenv(EnvResource, `{"name":"official","path":["./resource_pack/base"]}`)

	ctx, err := Load()
	if err != nil {
		t.Fatalf("Load() error = %v", err)
	}
	if ctx.ClientName != "MXU" || ctx.Controller["name"] != "Android" {
		t.Fatalf("unexpected context: %#v", ctx)
	}
	if Current().Resource["name"] != "official" {
		t.Fatalf("Current() was not updated: %#v", Current())
	}
}

func TestLoadAllowsMissingValues(t *testing.T) {
	ctx, err := Load()
	if err != nil {
		t.Fatalf("Load() error = %v", err)
	}
	if ctx.Controller != nil || ctx.Resource != nil {
		t.Fatalf("expected empty selections, got %#v", ctx)
	}
}

func TestLoadRejectsInvalidSelectionJSON(t *testing.T) {
	t.Setenv(EnvController, "not-json")
	if _, err := Load(); err == nil {
		t.Fatal("Load() error = nil, want invalid JSON error")
	}
}
