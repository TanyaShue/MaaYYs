// Package ocrtext 提供从 MaaFramework 识别详情中提取 OCR 文本与数字的通用逻辑。
//
// ctx.RunRecognition 返回的 RecognitionDetail 只有 Hit 表示是否命中，
// 真正的文本位于结构化 Results（best/filtered/all）或 DetailJson 中，需要显式解析。
package ocrtext

import (
	"encoding/json"
	"fmt"
	"regexp"
	"strconv"
	"strings"

	"github.com/MaaXYZ/maa-framework-go/v4"
)

// numberPattern 用于从 OCR 文本中提取数字，兼容 "12"、"12人" 这类结果。
var numberPattern = regexp.MustCompile(`[0-9]+`)

// ocrResult 对应识别详情 JSON 中的单条 OCR 结果。
type ocrResult struct {
	Text string `json:"text"`
}

// detailJSON 对应识别详情 JSON，用于兼容只提供 DetailJson 的 MaaFramework 版本。
type detailJSON struct {
	Best     *ocrResult  `json:"best"`
	Filtered []ocrResult `json:"filtered"`
	All      []ocrResult `json:"all"`
}

// Texts 按 best -> filtered -> all 的优先级返回识别详情中的 OCR 文本。
// 优先使用结构化 Results，不提供时回退解析 DetailJson。
// 返回值已去掉首尾空白，并剔除空文本与重复项。
func Texts(detail *maa.RecognitionDetail) []string {
	if detail == nil {
		return nil
	}

	texts := make([]string, 0, 4)
	if results := detail.Results; results != nil {
		if results.Best != nil {
			if best, ok := results.Best.AsOCR(); ok && best != nil {
				texts = append(texts, best.Text)
			}
		}
		for _, item := range results.Filtered {
			if item == nil {
				continue
			}
			if filtered, ok := item.AsOCR(); ok && filtered != nil {
				texts = append(texts, filtered.Text)
			}
		}
		for _, item := range results.All {
			if item == nil {
				continue
			}
			if all, ok := item.AsOCR(); ok && all != nil {
				texts = append(texts, all.Text)
			}
		}
	}

	// 兼容未提供结构化 Results、但仍提供 DetailJson 的 MaaFramework 版本。
	if len(texts) == 0 {
		var raw detailJSON
		if err := json.Unmarshal([]byte(detail.DetailJson), &raw); err == nil {
			if raw.Best != nil {
				texts = append(texts, raw.Best.Text)
			}
			for _, item := range raw.Filtered {
				texts = append(texts, item.Text)
			}
			for _, item := range raw.All {
				texts = append(texts, item.Text)
			}
		}
	}

	// 去掉空文本与重复候选，避免同一个文本被反复解析。
	seen := make(map[string]bool, len(texts))
	unique := texts[:0]
	for _, text := range texts {
		text = strings.TrimSpace(text)
		if text == "" || seen[text] {
			continue
		}
		seen[text] = true
		unique = append(unique, text)
	}
	return unique
}

// Number 返回候选文本中第一个能解析出的整数，以及它来自哪段文本。
func Number(texts []string) (value int, text string, ok bool) {
	for _, candidate := range texts {
		if parsed, ok := parseNumber(candidate); ok {
			return parsed, candidate, true
		}
	}
	return 0, "", false
}

// Describe 生成日志用的数字描述，文本带多余字符时附上原始 OCR 文本。
func Describe(value int, text string) string {
	number := strconv.Itoa(value)
	if text == number {
		return number
	}
	return fmt.Sprintf("%d (OCR原始文本: %q)", value, text)
}

// parseNumber 从 OCR 文本中解析数字，兼容全角数字与 "12人" 这类带多余字符的结果。
func parseNumber(text string) (int, bool) {
	match := numberPattern.FindString(normalizeDigits(text))
	if match == "" {
		return 0, false
	}
	value, err := strconv.Atoi(match)
	if err != nil {
		return 0, false
	}
	return value, true
}

// normalizeDigits 把全角数字转成半角数字，便于统一解析。
func normalizeDigits(text string) string {
	return strings.Map(func(r rune) rune {
		if r >= '０' && r <= '９' {
			return r - '０' + '0'
		}
		return r
	}, text)
}
