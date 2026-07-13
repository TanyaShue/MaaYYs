// Package projectinterface exposes the runtime context injected by a
// ProjectInterface V2 compatible client when it starts the agent process.
package projectinterface

import (
	"encoding/json"
	"fmt"
	"os"
	"sync"
)

const (
	EnvInterfaceVersion = "PI_INTERFACE_VERSION"
	EnvClientName       = "PI_CLIENT_NAME"
	EnvClientVersion    = "PI_CLIENT_VERSION"
	EnvClientLanguage   = "PI_CLIENT_LANGUAGE"
	EnvClientMaaFW      = "PI_CLIENT_MAAFW_VERSION"
	EnvProjectVersion   = "PI_VERSION"
	EnvController       = "PI_CONTROLLER"
	EnvResource         = "PI_RESOURCE"
)

// Context is the ProjectInterface runtime snapshot supplied by the client.
// Controller and Resource intentionally remain maps because the protocol
// permits controller- and project-specific extension fields.
type Context struct {
	InterfaceVersion string
	ClientName       string
	ClientVersion    string
	ClientLanguage   string
	ClientMaaFW      string
	ProjectVersion   string
	Controller       map[string]any
	Resource         map[string]any
}

var (
	current Context
	mu      sync.RWMutex
)

// Load reads all PI v2.5.0 agent environment variables. Missing variables are
// valid for compatibility with clients that do not provide the full context.
func Load() (Context, error) {
	ctx := Context{
		InterfaceVersion: os.Getenv(EnvInterfaceVersion),
		ClientName:       os.Getenv(EnvClientName),
		ClientVersion:    os.Getenv(EnvClientVersion),
		ClientLanguage:   os.Getenv(EnvClientLanguage),
		ClientMaaFW:      os.Getenv(EnvClientMaaFW),
		ProjectVersion:   os.Getenv(EnvProjectVersion),
	}

	if err := decodeOptionalJSON(EnvController, &ctx.Controller); err != nil {
		return Context{}, err
	}
	if err := decodeOptionalJSON(EnvResource, &ctx.Resource); err != nil {
		return Context{}, err
	}

	mu.Lock()
	current = ctx
	mu.Unlock()
	return ctx, nil
}

// Current returns the context loaded during agent startup.
func Current() Context {
	mu.RLock()
	defer mu.RUnlock()
	return current
}

func decodeOptionalJSON(name string, target *map[string]any) error {
	value := os.Getenv(name)
	if value == "" {
		return nil
	}
	if err := json.Unmarshal([]byte(value), target); err != nil {
		return fmt.Errorf("decode %s: %w", name, err)
	}
	return nil
}
