package daily_task_tracker

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sync"
	"time"

	"maa-yys-agent/global"
)

// DailyTaskTracker 用于跟踪任务是否在当天执行过的辅助类
type DailyTaskTracker struct {
	recordFile string
	lock       sync.Mutex
}

// NewDailyTaskTracker 创建新的DailyTaskTracker
func NewDailyTaskTracker() *DailyTaskTracker {
	cwd, _ := os.Getwd()
	assetsPath := filepath.Join(cwd, "assets")

	if _, err := os.Stat(assetsPath); os.IsNotExist(err) {
		os.MkdirAll(assetsPath, 0755)
	}

	recordFile := filepath.Join(assetsPath, "daily_tasks_record.json")
	fmt.Printf("DailyTaskTracker is using a single record file: '%s'\n", recordFile)

	return &DailyTaskTracker{
		recordFile: recordFile,
	}
}

// readRecords 从单个文件中读取所有设备的执行记录
func (t *DailyTaskTracker) readRecords() map[string]map[string]string {
	t.lock.Lock()
	defer t.lock.Unlock()

	data, err := os.ReadFile(t.recordFile)
	if err != nil {
		return make(map[string]map[string]string)
	}

	if len(data) == 0 {
		return make(map[string]map[string]string)
	}

	var records map[string]map[string]string
	if err := json.Unmarshal(data, &records); err != nil {
		return make(map[string]map[string]string)
	}

	return records
}

// writeRecords 将所有设备的执行记录写回单个文件
func (t *DailyTaskTracker) writeRecords(records map[string]map[string]string) {
	t.lock.Lock()
	defer t.lock.Unlock()

	data, err := json.MarshalIndent(records, "", "    ")
	if err != nil {
		fmt.Printf("序列化记录失败: %v\n", err)
		return
	}

	if err := os.WriteFile(t.recordFile, data, 0644); err != nil {
		fmt.Printf("写入记录文件失败: %v\n", err)
	}
}

// HasExecutedToday 检查指定任务对于当前设备今天是否已经执行过
func (t *DailyTaskTracker) HasExecutedToday(taskName string) bool {
	today := time.Now().Format("2006-01-02")
	currentDevice := global.GetDeviceName()

	allRecords := t.readRecords()

	deviceRecords, ok := allRecords[currentDevice]
	if !ok {
		return false
	}

	lastExecutionDate, ok := deviceRecords[taskName]
	if ok && lastExecutionDate == today {
		fmt.Printf("任务 '%s' 今天已经在设备 '%s' 上执行过，将跳过。\n", taskName, currentDevice)
		return true
	}

	return false
}

// RecordExecution 记录指定任务已在当前设备的命名空间下执行
func (t *DailyTaskTracker) RecordExecution(taskName string) {
	today := time.Now().Format("2006-01-02")
	currentDevice := global.GetDeviceName()

	allRecords := t.readRecords()

	if _, ok := allRecords[currentDevice]; !ok {
		allRecords[currentDevice] = make(map[string]string)
	}

	allRecords[currentDevice][taskName] = today

	t.writeRecords(allRecords)
	fmt.Printf("已为任务 '%s' 在设备 '%s' 上记录今天的执行日期：%s\n", taskName, currentDevice, today)
}