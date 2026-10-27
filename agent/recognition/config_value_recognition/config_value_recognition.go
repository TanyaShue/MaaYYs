package config_value_recognition

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"sync"

	"github.com/MaaXYZ/maa-framework-go/v4"
)

const (
	storeFileName        = "recognition_state.json"
	unknownControllerKey = "未知控制器"
)

var storeMu sync.Mutex

// ConfigValueWriteRecognition 写入/累加识别器
type ConfigValueWriteRecognition struct{}

// ConfigValueCheckRecognition 检查识别器
type ConfigValueCheckRecognition struct{}

type configValueParams struct {
	Key        string          `json:"key"`
	Value      json.RawMessage `json:"value"`
	Comparison string          `json:"comparison"`
}

// configStore 以控制器地址为主键，存放该控制器实例下的全部配置。
type configStore map[string]map[string]string

var _ maa.CustomRecognitionRunner = &ConfigValueWriteRecognition{}
var _ maa.CustomRecognitionRunner = &ConfigValueCheckRecognition{}

func (r *ConfigValueWriteRecognition) Run(ctx *maa.Context, arg *maa.CustomRecognitionArg) (*maa.CustomRecognitionResult, bool) {
	params, err := parseParams(arg)
	if err != nil {
		fmt.Printf("ConfigValueWriteRecognition: 解析参数失败: %v\n", err)
		return nil, false
	}
	if params.Key == "" {
		fmt.Println("ConfigValueWriteRecognition: key 不能为空")
		return nil, false
	}

	controllerAddress, err := resolveControllerAddress(ctx)
	if err != nil {
		fmt.Printf("ConfigValueWriteRecognition: 获取控制器地址失败: %v\n", err)
		return nil, false
	}

	storeMu.Lock()
	defer storeMu.Unlock()

	store, err := loadStore(controllerAddress)
	if err != nil {
		fmt.Printf("ConfigValueWriteRecognition: 读取存储失败: %v\n", err)
		return nil, false
	}

	entries := store[controllerAddress]
	if entries == nil {
		entries = make(map[string]string)
		store[controllerAddress] = entries
	}

	currentValue := entries[params.Key]
	newValue, err := resolveWriteValue(currentValue, params.Value)
	if err != nil {
		fmt.Printf("ConfigValueWriteRecognition: 计算写入值失败: %v\n", err)
		return nil, false
	}

	entries[params.Key] = newValue
	if err := saveStore(store); err != nil {
		fmt.Printf("ConfigValueWriteRecognition: 保存存储失败: %v\n", err)
		return nil, false
	}

	fmt.Printf("ConfigValueWriteRecognition: [%s] %s => %s\n", controllerAddress, params.Key, newValue)
	return &maa.CustomRecognitionResult{Box: maa.Rect{0, 0, 0, 0}}, true
}

func (r *ConfigValueCheckRecognition) Run(ctx *maa.Context, arg *maa.CustomRecognitionArg) (*maa.CustomRecognitionResult, bool) {
	params, err := parseParams(arg)
	if err != nil {
		fmt.Printf("ConfigValueCheckRecognition: 解析参数失败: %v\n", err)
		return nil, false
	}
	if params.Key == "" {
		fmt.Println("ConfigValueCheckRecognition: key 不能为空")
		return nil, false
	}

	controllerAddress, err := resolveControllerAddress(ctx)
	if err != nil {
		fmt.Printf("ConfigValueCheckRecognition: 获取控制器地址失败: %v\n", err)
		return nil, false
	}

	storeMu.Lock()
	defer storeMu.Unlock()

	store, err := loadStore(controllerAddress)
	if err != nil {
		fmt.Printf("ConfigValueCheckRecognition: 读取存储失败: %v\n", err)
		return nil, false
	}

	currentValue := store[controllerAddress][params.Key]
	if currentValue == "" {
		currentValue = "0"
	}

	currentNum, err := parseNumber(currentValue)
	if err != nil {
		fmt.Printf("ConfigValueCheckRecognition: 当前值不是数字: controller=%s key=%s value=%s\n", controllerAddress, params.Key, currentValue)
		return nil, false
	}

	targetNum, err := parseNumberFromRaw(params.Value)
	if err != nil {
		fmt.Printf("ConfigValueCheckRecognition: 阈值不是数字: controller=%s key=%s\n", controllerAddress, params.Key)
		return nil, false
	}

	comparison := normalizeComparison(params.Comparison)
	if comparison == "" {
		fmt.Printf("ConfigValueCheckRecognition: 不支持的比较符号: %s\n", params.Comparison)
		return nil, false
	}

	if compareNumbers(currentNum, targetNum, comparison) {
		fmt.Printf("ConfigValueCheckRecognition: [%s] %s 当前值 %s %s %s, 返回 true\n", controllerAddress, params.Key, currentValue, comparison, formatNumber(targetNum))
		return &maa.CustomRecognitionResult{Box: maa.Rect{0, 0, 0, 0}}, true
	}

	fmt.Printf("ConfigValueCheckRecognition: [%s] %s 当前值 %s 不满足 %s %s, 返回 false\n", controllerAddress, params.Key, currentValue, comparison, formatNumber(targetNum))
	return nil, false
}

func parseParams(arg *maa.CustomRecognitionArg) (*configValueParams, error) {
	var params configValueParams
	if arg != nil && arg.CustomRecognitionParam != "" {
		if err := json.Unmarshal([]byte(arg.CustomRecognitionParam), &params); err != nil {
			return nil, err
		}
	}
	return &params, nil
}

// resolveControllerAddress 从当前 Tasker 绑定的 Controller 信息中获取实例地址。
func resolveControllerAddress(ctx *maa.Context) (string, error) {
	if ctx == nil {
		return unknownControllerKey, nil
	}

	tasker := ctx.GetTasker()
	if tasker == nil {
		return unknownControllerKey, nil
	}

	controller := tasker.GetController()
	if controller == nil {
		return unknownControllerKey, nil
	}

	infoJSON, err := controller.GetInfo()
	if err != nil {
		fmt.Printf("ConfigValueRecognition: 获取控制器信息失败，使用默认控制器: %v\n", err)
		return unknownControllerKey, nil
	}

	info := make(map[string]any)
	if err := json.Unmarshal([]byte(infoJSON), &info); err != nil {
		fmt.Printf("ConfigValueRecognition: 解析控制器信息失败，使用默认控制器: %v\n", err)
		return unknownControllerKey, nil
	}

	address := firstControllerAddress(info, "address", "adb_serial")
	if address != "" {
		return address, nil
	}

	for _, nestedKey := range []string{"adb", "controller"} {
		nested, ok := info[nestedKey].(map[string]any)
		if !ok {
			continue
		}
		address = firstControllerAddress(nested, "address", "adb_serial")
		if address != "" {
			return address, nil
		}
	}

	return unknownControllerKey, nil
}

func firstControllerAddress(info map[string]any, keys ...string) string {
	for _, key := range keys {
		value, ok := info[key].(string)
		if !ok {
			continue
		}
		if address := strings.TrimSpace(value); address != "" {
			return address
		}
	}
	return ""
}

func projectRoot() string {
	if cwd, err := os.Getwd(); err == nil {
		if _, err := os.Stat(filepath.Join(cwd, "assets")); err == nil {
			return cwd
		}
	}

	exe, err := os.Executable()
	if err != nil {
		return "."
	}

	return filepath.Clean(filepath.Join(filepath.Dir(exe), ".."))
}

func storePath() string {
	return filepath.Join(projectRoot(), "assets", storeFileName)
}

func loadStore(controllerAddress string) (configStore, error) {
	path := storePath()
	data, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			return make(configStore), nil
		}
		return nil, err
	}

	if len(bytes.TrimSpace(data)) == 0 {
		return make(configStore), nil
	}

	var rawStore map[string]json.RawMessage
	if err := json.Unmarshal(data, &rawStore); err != nil {
		return nil, err
	}

	store := make(configStore)
	legacyEntries := make(map[string]string)

	for key, rawValue := range rawStore {
		rawValue = bytes.TrimSpace(rawValue)
		if len(rawValue) == 0 || bytes.Equal(rawValue, []byte("null")) {
			continue
		}

		// 旧版存储是扁平的 string map，读取时迁移到当前控制器地址下。
		if rawValue[0] != '{' {
			var value string
			if err := json.Unmarshal(rawValue, &value); err != nil {
				return nil, fmt.Errorf("解析旧版配置项 %q 失败: %w", key, err)
			}
			legacyEntries[key] = value
			continue
		}

		entries := make(map[string]string)
		if err := json.Unmarshal(rawValue, &entries); err != nil {
			return nil, fmt.Errorf("解析控制器 %q 的配置失败: %w", key, err)
		}
		store[key] = entries
	}

	if len(legacyEntries) > 0 {
		entries := store[controllerAddress]
		if entries == nil {
			entries = make(map[string]string)
			store[controllerAddress] = entries
		}
		for key, value := range legacyEntries {
			if _, exists := entries[key]; !exists {
				entries[key] = value
			}
		}
	}

	return store, nil
}

func saveStore(store configStore) error {
	path := storePath()
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}

	data, err := json.MarshalIndent(store, "", "  ")
	if err != nil {
		return err
	}

	return os.WriteFile(path, data, 0o644)
}

func resolveWriteValue(currentValue string, rawValue json.RawMessage) (string, error) {
	if special, ok := parseSpecialWriteValue(rawValue); ok {
		currentNum, err := parseNumber(currentValue)
		if err != nil {
			currentNum = 0
		}
		return formatNumber(currentNum + special), nil
	}

	return rawMessageToString(rawValue)
}

func parseSpecialWriteValue(rawValue json.RawMessage) (float64, bool) {
	value, err := rawMessageToString(rawValue)
	if err != nil {
		return 0, false
	}

	switch strings.ToLower(strings.TrimSpace(value)) {
	case "add", "+", "++", "+1", "inc", "increase", "plus":
		return 1, true
	case "sub", "-", "--", "-1", "dec", "decrease", "minus":
		return -1, true
	default:
		return 0, false
	}
}

func rawMessageToString(rawValue json.RawMessage) (string, error) {
	rawValue = bytes.TrimSpace(rawValue)
	if len(rawValue) == 0 || bytes.Equal(rawValue, []byte("null")) {
		return "", nil
	}

	var text string
	if err := json.Unmarshal(rawValue, &text); err == nil {
		return text, nil
	}

	var number json.Number
	decoder := json.NewDecoder(bytes.NewReader(rawValue))
	decoder.UseNumber()
	if err := decoder.Decode(&number); err == nil {
		return number.String(), nil
	}

	var boolean bool
	if err := json.Unmarshal(rawValue, &boolean); err == nil {
		return strconv.FormatBool(boolean), nil
	}

	return "", fmt.Errorf("unsupported value type: %s", string(rawValue))
}

func parseNumberFromRaw(rawValue json.RawMessage) (float64, error) {
	value, err := rawMessageToString(rawValue)
	if err != nil {
		return 0, err
	}
	return parseNumber(value)
}

func parseNumber(value string) (float64, error) {
	return strconv.ParseFloat(strings.TrimSpace(value), 64)
}

func formatNumber(value float64) string {
	return strconv.FormatFloat(value, 'f', -1, 64)
}

func normalizeComparison(comparison string) string {
	switch strings.TrimSpace(comparison) {
	case "", "<":
		return "<"
	case ">":
		return ">"
	case "==":
		return "=="
	case "<=":
		return "<="
	case ">=":
		return ">="
	case "!=":
		return "!="
	default:
		return ""
	}
}

func compareNumbers(currentNum, targetNum float64, comparison string) bool {
	switch comparison {
	case "<":
		return currentNum < targetNum
	case ">":
		return currentNum > targetNum
	case "==":
		return currentNum == targetNum
	case "<=":
		return currentNum <= targetNum
	case ">=":
		return currentNum >= targetNum
	case "!=":
		return currentNum != targetNum
	default:
		return false
	}
}
