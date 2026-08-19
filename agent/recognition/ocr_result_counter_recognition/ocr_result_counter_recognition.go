package ocr_result_counter_recognition

import (
	"bytes"
	"encoding/json"
	"fmt"
	"math"
	"strconv"
	"strings"
	"sync"

	maa "github.com/MaaXYZ/maa-framework-go/v4"
)

// OCRResultCounterRecognition 统计指定 OCR 节点的 best 文本连续出现次数。
type OCRResultCounterRecognition struct {
	mu       sync.Mutex
	lastNode string
	lastText string
	count    int
}

type params struct {
	RecognitionNode string          `json:"recognition_node"`
	TargetCount     json.RawMessage `json:"target_count"`
}

type ocrDetail struct {
	Best *struct {
		Box  maa.Rect `json:"box"`
		Text string   `json:"text"`
	} `json:"best"`
}

type resultDetail struct {
	RecognitionNode string `json:"recognition_node"`
	Text            string `json:"text"`
	Count           int    `json:"count"`
	TargetCount     int    `json:"target_count"`
}

var _ maa.CustomRecognitionRunner = &OCRResultCounterRecognition{}

// Run 使用当前自定义识别节点收到的图片运行指定 OCR 节点，并统计 best 文本。
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
		r.resetConsecutiveCount()
		return nil, false
	}

	detail, err := ctx.RunRecognition(recognitionNode, arg.Img, nil)
	if err != nil {
		r.resetConsecutiveCount()
		return nil, false
	}
	if detail == nil || !detail.Hit {
		r.resetConsecutiveCount()
		return nil, false
	}

	text, box, ok := bestOCRResult(detail)
	if !ok {
		r.resetConsecutiveCount()
		return nil, false
	}

	count := r.updateConsecutiveCount(recognitionNode, text)
	if count < targetCount {
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

func bestOCRResult(detail *maa.RecognitionDetail) (string, maa.Rect, bool) {
	if detail == nil {
		return "", maa.Rect{}, false
	}

	if detail.Results != nil && detail.Results.Best != nil {
		if best, ok := detail.Results.Best.AsOCR(); ok && best != nil {
			text := strings.TrimSpace(best.Text)
			if text != "" {
				return text, best.Box, true
			}
		}
	}

	// 兼容未提供结构化 Results、但仍提供 DetailJson 的 MaaFramework 版本。
	var raw ocrDetail
	if err := json.Unmarshal([]byte(detail.DetailJson), &raw); err != nil || raw.Best == nil {
		return "", maa.Rect{}, false
	}
	text := strings.TrimSpace(raw.Best.Text)
	if text == "" {
		return "", maa.Rect{}, false
	}
	return text, raw.Best.Box, true
}

func (r *OCRResultCounterRecognition) updateConsecutiveCount(node, text string) int {
	r.mu.Lock()
	defer r.mu.Unlock()

	if r.lastNode == node && r.lastText == text {
		r.count++
		return r.count
	}

	r.lastNode = node
	r.lastText = text
	r.count = 1
	return r.count
}

func (r *OCRResultCounterRecognition) resetConsecutiveCount() {
	r.mu.Lock()
	defer r.mu.Unlock()

	r.lastNode = ""
	r.lastText = ""
	r.count = 0
}
