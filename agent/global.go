package main

import (
	"fmt"
	"sync"
)

var (
	deviceName     = "default_device"
	deviceNameLock sync.RWMutex
)

// SetDeviceName 设置全局的设备名称
func SetDeviceName(name string) {
	deviceNameLock.Lock()
	defer deviceNameLock.Unlock()
	deviceName = name
	fmt.Printf("[Global] Device name set to: %s\n", name)
}

// GetDeviceName 获取当前设备名称
func GetDeviceName() string {
	deviceNameLock.RLock()
	defer deviceNameLock.RUnlock()
	return deviceName
}