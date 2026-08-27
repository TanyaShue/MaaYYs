package ocr_result_counter_recognition

import (
	"bytes"
	"encoding/json"
	"fmt"
	"math"
	"sort"
	"strconv"
	"strings"
	"sync"

	maa "github.com/MaaXYZ/maa-framework-go/v4"
)

// OCRResultCounterRecognition 统计指定 OCR 节点 OCR 结果的出现次数。
type OCRResultCounterRecognition struct {
	mu       sync.Mutex
	lastNode string
	counts   map[string]int
}

type params struct {
	RecognitionNode string          `json:"recognition_node"`
	TargetCount     json.RawMessage `json:"target_count"`
}

type ocrDetail struct {
	All      []ocrResult `json:"all"`
	Filtered []ocrResult `json:"filtered"`
	Best     *ocrResult  `json:"best"`
}

type ocrResult struct {
	Box   maa.Rect `json:"box"`
	Text  string   `json:"text"`
	Score float64  `json:"score"`
}

type resultDetail struct {
	RecognitionNode string `json:"recognition_node"`
	Text            string `json:"text"`
	Count           int    `json:"count"`
	TargetCount     int    `json:"target_count"`
}

var _ maa.CustomRecognitionRunner = &OCRResultCounterRecognition{}

// Run 使用当前自定义识别节点收到的图片运行指定 OCR 节点，并统计评分前三的文本。
func (r *OCRResultCounterRecognition) Run(ctx *maa.Context, arg *maa.CustomRecognitionArg) (*maa.CustomRecognitionResult, bool) {
	if ctx == nil || arg == nil {
		fmt.Println("OCRResultCounterRecognition: context 或参数为空")
		return nil, false
	}

	recognitionNode, targetCount, err := parseParams(arg.CustomRecognitionParam)
	if err != nil {
		fmt.Printf("OCRResultCounterRecognition: 解析参数失败: %v\n", err)
		return nil, false
	}
	if arg.Img == nil {
		fmt.Println("OCRResultCounterRecognition: 当前识别图片为空")
		r.resetCounts()
		return nil, false
	}

	detail, err := ctx.RunRecognition(recognitionNode, arg.Img, nil)
	if err != nil {
		r.resetCounts()
		return nil, false
	}
	if detail == nil || !detail.Hit {
		r.resetCounts()
		return nil, false
	}

	results := top3OCRResults(detail)
	if len(results) == 0 {
		r.resetCounts()
		return nil, false
	}

	text, box, count, ok := r.updateCounts(recognitionNode, results, targetCount)
	if !ok {
		return nil, false
	}

	detailJSON, err := json.Marshal(resultDetail{
		RecognitionNode: recognitionNode,
		Text:            text,
		Count:           count,
		TargetCount:     targetCount,
	})
	if err != nil {
		fmt.Printf("OCRResultCounterRecognition: 序列化结果详情失败: %v\n", err)
		return nil, false
	}

	return &maa.CustomRecognitionResult{
		Box:    box,
		Detail: string(detailJSON),
	}, true
}

func parseParams(raw string) (string, int, error) {
	if strings.TrimSpace(raw) == "" {
		return "", 0, fmt.Errorf("custom_recognition_param 不能为空")
	}

	var p params
	if err := json.Unmarshal([]byte(raw), &p); err != nil {
		return "", 0, err
	}

	node := strings.TrimSpace(p.RecognitionNode)
	if node == "" {
		return "", 0, fmt.Errorf("recognition_node 不能为空")
	}

	targetCount, err := parsePositiveInt(p.TargetCount)
	if err != nil {
		return "", 0, fmt.Errorf("target_count 无效: %w", err)
	}
	return node, targetCount, nil
}

func parsePositiveInt(raw json.RawMessage) (int, error) {
	raw = bytes.TrimSpace(raw)
	if len(raw) == 0 || bytes.Equal(raw, []byte("null")) {
		return 0, fmt.Errorf("不能为空")
	}

	var value any
	decoder := json.NewDecoder(bytes.NewReader(raw))
	decoder.UseNumber()
	if err := decoder.Decode(&value); err != nil {
		return 0, err
	}

	var numberText string
	switch v := value.(type) {
	case json.Number:
		numberText = v.String()
	case string:
		numberText = strings.TrimSpace(v)
	default:
		return 0, fmt.Errorf("必须是数字或数字字符串")
	}

	number, err := strconv.ParseFloat(numberText, 64)
	if err != nil || math.IsInf(number, 0) || math.IsNaN(number) {
		return 0, fmt.Errorf("%q 不是有效数字", numberText)
	}
	if number < 1 || math.Trunc(number) != number || number > float64(^uint(0)>>1) {
		return 0, fmt.Errorf("必须是大于等于 1 的整数")
	}
	return int(number), nil
}

func top3OCRResults(detail *maa.RecognitionDetail) []ocrResult {
	if detail == nil {
		return nil
	}

	results := make([]ocrResult, 0)
	if detail.Results != nil {
		for _, item := range detail.Results.All {
			if item == nil {
				continue
			}
			if result, ok := item.AsOCR(); ok && result != nil && strings.TrimSpace(result.Text) != "" {
				results = append(results, ocrResult{Box: result.Box, Text: strings.TrimSpace(result.Text), Score: result.Score})
			}
		}
		if len(results) == 0 && detail.Results.Best != nil {
			if best, ok := detail.Results.Best.AsOCR(); ok && best != nil && strings.TrimSpace(best.Text) != "" {
				results = append(results, ocrResult{Box: best.Box, Text: strings.TrimSpace(best.Text), Score: best.Score})
			}
		}
	}

	// 兼容未提供结构化 Results、但仍提供 DetailJson 的 MaaFramework 版本。
	var raw ocrDetail
	if len(results) == 0 {
		if err := json.Unmarshal([]byte(detail.DetailJson), &raw); err != nil {
			return nil
		}
		results = raw.All
		if len(results) == 0 {
			results = raw.Filtered
		}
		if len(results) == 0 && raw.Best != nil {
			results = []ocrResult{*raw.Best}
		}
	}
	for i := range results {
		results[i].Text = strings.TrimSpace(results[i].Text)
	}
	results = slicesWithoutEmptyText(results)
	sort.SliceStable(results, func(i, j int) bool { return results[i].Score > results[j].Score })
	if len(results) > 3 {
		results = results[:3]
	}
	return results
}

func slicesWithoutEmptyText(results []ocrResult) []ocrResult {
	filtered := results[:0]
	for _, result := range results {
		if result.Text != "" {
			filtered = append(filtered, result)
		}
	}
	return filtered
}

func (r *OCRResultCounterRecognition) updateCounts(node string, results []ocrResult, targetCount int) (string, maa.Rect, int, bool) {
	r.mu.Lock()
	defer r.mu.Unlock()

	if r.lastNode != node || r.counts == nil {
		r.lastNode = node
		r.counts = make(map[string]int)
	}
	var matched *ocrResult
	for i := range results {
		result := &results[i]
		r.counts[result.Text]++
		if matched == nil && r.counts[result.Text] > targetCount {
			matched = result
		}
	}
	if matched != nil {
		count := r.counts[matched.Text]
		// 命中后清空本轮累计，下一次识别重新开始计数。
		r.lastNode = ""
		r.counts = nil
		return matched.Text, matched.Box, count, true
	}
	return "", maa.Rect{}, 0, false
}

func (r *OCRResultCounterRecognition) resetCounts() {
	r.mu.Lock()
	defer r.mu.Unlock()

	r.lastNode = ""
	r.counts = nil
}
