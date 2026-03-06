// Package global provides global variables and helper functions for the MaaYYs Agent.
package global

import (
	"fmt"
	"sync"
)

var (
	deviceName     = "default_device"
	deviceNameLock sync.RWMutex
)

// SetDeviceName sets the global device name
func SetDeviceName(name string) {
	deviceNameLock.Lock()
	defer deviceNameLock.Unlock()
	deviceName = name
	fmt.Printf("[Global] Device name set to: %s\n", name)
}

// GetDeviceName returns the current device name
func GetDeviceName() string {
	deviceNameLock.RLock()
	defer deviceNameLock.RUnlock()
	return deviceName
}