package config_value_recognition

import (
	"encoding/json"
	"fmt"
	"strings"
	"time"

	maa "github.com/MaaXYZ/maa-framework-go/v4"
)

const (
	weekStatusComparisonWeek  = "week"
	weekStatusComparisonMonth = "month"
	weekStatusComparisonDay   = "day"

	weekStatusMatchSame      = "same"
	weekStatusMatchDifferent = "different"
)

// WeekStatusWriteRecognition 将当前时间写入指定状态键。
type WeekStatusWriteRecognition struct{}

// WeekStatusCheckRecognition 检查已存储时间与当前时间是否处于同一周期。
type WeekStatusCheckRecognition struct{}

type weekStatusWriteParams struct {
	Key string `json:"key"`
}

type weekStatusCheckParams struct {
	Key        string `json:"key"`
	Comparison string `json:"comparison"`
	Match      string `json:"match"`
}

var _ maa.CustomRecognitionRunner = &WeekStatusWriteRecognition{}
var _ maa.CustomRecognitionRunner = &WeekStatusCheckRecognition{}

func (r *WeekStatusWriteRecognition) Run(ctx *maa.Context, arg *maa.CustomRecognitionArg) (*maa.CustomRecognitionResult, bool) {
	params, err := parseWeekStatusWriteParams(arg)
	if err != nil {
		fmt.Printf("WeekStatusWriteRecognition: 解析参数失败: %v\n", err)
		return nil, false
	}

	key := strings.TrimSpace(params.Key)
	if key == "" {
		fmt.Println("WeekStatusWriteRecognition: key 不能为空")
		return nil, false
	}

	controllerAddress, err := resolveControllerAddress(ctx)
	if err != nil {
		fmt.Printf("WeekStatusWriteRecognition: 获取控制器地址失败: %v\n", err)
		return nil, false
	}

	storeMu.Lock()
	defer storeMu.Unlock()

	store, err := loadStore(controllerAddress)
	if err != nil {
		fmt.Printf("WeekStatusWriteRecognition: 读取存储失败: %v\n", err)
		return nil, false
	}

	entries := store[controllerAddress]
	if entries == nil {
		entries = make(map[string]string)
		store[controllerAddress] = entries
	}

	newValue := time.Now().Format(time.RFC3339)
	entries[key] = newValue
	if err := saveStore(store); err != nil {
		fmt.Printf("WeekStatusWriteRecognition: 保存存储失败: %v\n", err)
		return nil, false
	}

	fmt.Printf("WeekStatusWriteRecognition: [%s] %s => %s\n", controllerAddress, key, newValue)
	return &maa.CustomRecognitionResult{Box: maa.Rect{0, 0, 0, 0}}, true
}

func (r *WeekStatusCheckRecognition) Run(ctx *maa.Context, arg *maa.CustomRecognitionArg) (*maa.CustomRecognitionResult, bool) {
	params, err := parseWeekStatusCheckParams(arg)
	if err != nil {
		fmt.Printf("WeekStatusCheckRecognition: 解析参数失败: %v\n", err)
		return nil, false
	}

	key := strings.TrimSpace(params.Key)
	if key == "" {
		fmt.Println("WeekStatusCheckRecognition: key 不能为空")
		return nil, false
	}

	comparison := normalizeWeekStatusComparison(params.Comparison)
	if comparison == "" {
		fmt.Printf("WeekStatusCheckRecognition: 不支持的比较方式: %s\n", params.Comparison)
		return nil, false
	}

	match := normalizeWeekStatusMatch(params.Match)
	if match == "" {
		fmt.Printf("WeekStatusCheckRecognition: 不支持的匹配方式: %s\n", params.Match)
		return nil, false
	}

	controllerAddress, err := resolveControllerAddress(ctx)
	if err != nil {
		fmt.Printf("WeekStatusCheckRecognition: 获取控制器地址失败: %v\n", err)
		return nil, false
	}

	storeMu.Lock()
	defer storeMu.Unlock()

	store, err := loadStore(controllerAddress)
	if err != nil {
		fmt.Printf("WeekStatusCheckRecognition: 读取存储失败: %v\n", err)
		return nil, false
	}

	value := store[controllerAddress][key]
	if value == "" {
		fmt.Printf("WeekStatusCheckRecognition: [%s] %s 没有已写入的时间\n", controllerAddress, key)
		return nil, false
	}

	storedAt, err := time.Parse(time.RFC3339, value)
	if err != nil {
		fmt.Printf("WeekStatusCheckRecognition: [%s] %s 时间格式无效: %s\n", controllerAddress, key, value)
		return nil, false
	}

	now := time.Now()
	storedAt = storedAt.In(now.Location())
	inSamePeriod := sameWeekStatusPeriod(storedAt, now, comparison)
	result := inSamePeriod == (match == weekStatusMatchSame)
	if result {
		fmt.Printf("WeekStatusCheckRecognition: [%s] %s 已存储时间 %s 与当前时间 %s 同一%s=%t, 要求=%s, 返回 true\n", controllerAddress, key, value, now.Format(time.RFC3339), weekStatusComparisonLabel(comparison), inSamePeriod, match)
		return &maa.CustomRecognitionResult{Box: maa.Rect{0, 0, 0, 0}}, true
	}

	fmt.Printf("WeekStatusCheckRecognition: [%s] %s 已存储时间 %s 与当前时间 %s 同一%s=%t, 要求=%s, 返回 false\n", controllerAddress, key, value, now.Format(time.RFC3339), weekStatusComparisonLabel(comparison), inSamePeriod, match)
	return nil, false
}

func parseWeekStatusWriteParams(arg *maa.CustomRecognitionArg) (*weekStatusWriteParams, error) {
	var params weekStatusWriteParams
	if arg != nil && arg.CustomRecognitionParam != "" {
		if err := json.Unmarshal([]byte(arg.CustomRecognitionParam), &params); err != nil {
			return nil, err
		}
	}
	return &params, nil
}

func parseWeekStatusCheckParams(arg *maa.CustomRecognitionArg) (*weekStatusCheckParams, error) {
	var params weekStatusCheckParams
	if arg != nil && arg.CustomRecognitionParam != "" {
		if err := json.Unmarshal([]byte(arg.CustomRecognitionParam), &params); err != nil {
			return nil, err
		}
	}
	return &params, nil
}

func normalizeWeekStatusComparison(comparison string) string {
	switch strings.ToLower(strings.TrimSpace(comparison)) {
	case "", weekStatusComparisonWeek:
		return weekStatusComparisonWeek
	case weekStatusComparisonMonth:
		return weekStatusComparisonMonth
	case weekStatusComparisonDay:
		return weekStatusComparisonDay
	default:
		return ""
	}
}

func normalizeWeekStatusMatch(match string) string {
	switch strings.ToLower(strings.TrimSpace(match)) {
	case "", weekStatusMatchSame:
		return weekStatusMatchSame
	case weekStatusMatchDifferent:
		return weekStatusMatchDifferent
	default:
		return ""
	}
}

func sameWeekStatusPeriod(storedAt, now time.Time, comparison string) bool {
	switch comparison {
	case weekStatusComparisonWeek:
		storedYear, storedWeek := storedAt.ISOWeek()
		nowYear, nowWeek := now.ISOWeek()
		return storedYear == nowYear && storedWeek == nowWeek
	case weekStatusComparisonMonth:
		return storedAt.Year() == now.Year() && storedAt.Month() == now.Month()
	case weekStatusComparisonDay:
		return storedAt.Year() == now.Year() && storedAt.YearDay() == now.YearDay()
	default:
		return false
	}
}

func weekStatusComparisonLabel(comparison string) string {
	switch comparison {
	case weekStatusComparisonWeek:
		return "周"
	case weekStatusComparisonMonth:
		return "月"
	case weekStatusComparisonDay:
		return "天"
	default:
		return "周期"
	}
}
