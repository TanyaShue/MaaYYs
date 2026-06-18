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

const storeFileName = "recognition_state.json"

var storeMu sync.Mutex

// ConfigValueWriteRecognition 写入/累加识别器
type ConfigValueWriteRecognition struct{}

// ConfigValueCheckRecognition 检查识别器
type ConfigValueCheckRecognition struct{}

type configValueParams struct {
	Key        string          `json:"key"`
	Value      json.RawMessage `json:"value"`
	Comparison string          `json:"comparison"`
	Compare    string          `json:"compare"`
	Operator   string          `json:"operator"`
	Mode       string          `json:"mode"`
}

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

	storeMu.Lock()
	defer storeMu.Unlock()

	store, err := loadStore()
	if err != nil {
		fmt.Printf("ConfigValueWriteRecognition: 读取存储失败: %v\n", err)
		return nil, false
	}

	currentValue := store[params.Key]
	newValue, err := resolveWriteValue(currentValue, params.Value)
	if err != nil {
		fmt.Printf("ConfigValueWriteRecognition: 计算写入值失败: %v\n", err)
		return nil, false
	}

	store[params.Key] = newValue
	if err := saveStore(store); err != nil {
		fmt.Printf("ConfigValueWriteRecognition: 保存存储失败: %v\n", err)
		return nil, false
	}

	fmt.Printf("ConfigValueWriteRecognition: %s => %s\n", params.Key, newValue)
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

	storeMu.Lock()
	defer storeMu.Unlock()

	store, err := loadStore()
	if err != nil {
		fmt.Printf("ConfigValueCheckRecognition: 读取存储失败: %v\n", err)
		return nil, false
	}

	currentValue := store[params.Key]
	if currentValue == "" {
		currentValue = "0"
	}

	currentNum, err := parseNumber(currentValue)
	if err != nil {
		fmt.Printf("ConfigValueCheckRecognition: 当前值不是数字: key=%s value=%s\n", params.Key, currentValue)
		return nil, false
	}

	targetNum, err := parseNumberFromRaw(params.Value)
	if err != nil {
		fmt.Printf("ConfigValueCheckRecognition: 阈值不是数字: key=%s\n", params.Key)
		return nil, false
	}

	comparison := normalizeComparison(params.comparison())
	if comparison == "" {
		fmt.Printf("ConfigValueCheckRecognition: 不支持的比较方式: %s\n", params.comparison())
		return nil, false
	}

	if compareNumbers(currentNum, targetNum, comparison) {
		fmt.Printf("ConfigValueCheckRecognition: %s 当前值 %s %s %s, 返回 true\n", params.Key, currentValue, comparison, formatNumber(targetNum))
		return &maa.CustomRecognitionResult{Box: maa.Rect{0, 0, 0, 0}}, true
	}

	fmt.Printf("ConfigValueCheckRecognition: %s 当前值 %s 不满足 %s %s, 返回 false\n", params.Key, currentValue, comparison, formatNumber(targetNum))
	return nil, false
}

func (p *configValueParams) comparison() string {
	switch {
	case p.Comparison != "":
		return p.Comparison
	case p.Compare != "":
		return p.Compare
	case p.Operator != "":
		return p.Operator
	case p.Mode != "":
		return p.Mode
	default:
		return "<"
	}
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

func loadStore() (map[string]string, error) {
	path := storePath()
	data, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			return map[string]string{}, nil
		}
		return nil, err
	}

	if len(bytes.TrimSpace(data)) == 0 {
		return map[string]string{}, nil
	}

	store := make(map[string]string)
	if err := json.Unmarshal(data, &store); err != nil {
		return nil, err
	}
	return store, nil
}

func saveStore(store map[string]string) error {
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
	switch strings.ToLower(strings.TrimSpace(comparison)) {
	case "", "<", "lt", "less", "小于":
		return "<"
	case ">", "gt", "greater", "大于":
		return ">"
	case "=", "==", "eq", "equal", "equals", "等于":
		return "=="
	case "<=", "=<", "le", "lte", "less_equal", "less than or equal", "小于等于", "不大于":
		return "<="
	case ">=", "=>", "ge", "gte", "greater_equal", "greater than or equal", "大于等于", "不小于":
		return ">="
	case "!=", "<>", "ne", "neq", "not_equal", "not equal", "不等于":
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
