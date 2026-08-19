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

type countUpdate struct {
	PreviousNode  string
	PreviousText  string
	PreviousCount int
	Count         int
	Consecutive   bool
}

type counterState struct {
	Node  string
	Text  string
	Count int
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
	fmt.Printf(
		"OCRResultCounterRecognition[DEBUG]: 开始识别 task_id=%d current_task=%q recognition_node=%q target_count=%d roi=%v\n",
		arg.TaskID,
		arg.CurrentTaskName,
		recognitionNode,
		targetCount,
		arg.Roi,
	)
	if arg.Img == nil {
		fmt.Println("OCRResultCounterRecognition: 当前识别图片为空")
		r.resetConsecutiveCountWithDebug("当前识别图片为空")
		return nil, false
	}

	detail, err := ctx.RunRecognition(recognitionNode, arg.Img, nil)
	if err != nil {
		fmt.Printf("OCRResultCounterRecognition: 运行识别节点 %q 失败: %v\n", recognitionNode, err)
		r.resetConsecutiveCountWithDebug("识别 API 调用失败")
		return nil, false
	}
	if detail != nil {
		fmt.Printf(
			"OCRResultCounterRecognition[DEBUG]: 识别 API 返回 node=%q algorithm=%q hit=%t box=%v detail_json=%q\n",
			recognitionNode,
			detail.Algorithm,
			detail.Hit,
			detail.Box,
			detail.DetailJson,
		)
	} else {
		fmt.Printf("OCRResultCounterRecognition[DEBUG]: 识别 API 返回 node=%q detail=nil\n", recognitionNode)
	}
	if detail == nil || !detail.Hit {
		fmt.Printf("OCRResultCounterRecognition: 识别节点 %q 未命中\n", recognitionNode)
		r.resetConsecutiveCountWithDebug("识别节点未命中")
		return nil, false
	}

	text, box, ok := bestOCRResult(detail)
	if !ok {
		fmt.Printf("OCRResultCounterRecognition: 识别节点 %q 没有有效的 OCR best 结果\n", recognitionNode)
		r.resetConsecutiveCountWithDebug("没有有效的 OCR best 结果")
		return nil, false
	}
	fmt.Printf(
		"OCRResultCounterRecognition[DEBUG]: 当前 OCR best 结果 node=%q text=%q box=%v target_count=%d\n",
		recognitionNode,
		text,
		box,
		targetCount,
	)

	update := r.updateConsecutiveCount(recognitionNode, text)
	reached := update.Count >= targetCount
	fmt.Printf(
		"OCRResultCounterRecognition[DEBUG]: 更新连续计数 previous_node=%q previous_text=%q previous_count=%d current_node=%q current_text=%q consecutive=%t current_count=%d target_count=%d reached=%t\n",
		update.PreviousNode,
		update.PreviousText,
		update.PreviousCount,
		recognitionNode,
		text,
		update.Consecutive,
		update.Count,
		targetCount,
		reached,
	)
	if !reached {
		fmt.Printf("OCRResultCounterRecognition: 节点 %q 的结果 %q 连续出现 %d/%d 次，返回 false\n", recognitionNode, text, update.Count, targetCount)
		return nil, false
	}

	detailJSON, err := json.Marshal(resultDetail{
		RecognitionNode: recognitionNode,
		Text:            text,
		Count:           update.Count,
		TargetCount:     targetCount,
	})
	if err != nil {
		fmt.Printf("OCRResultCounterRecognition: 序列化结果详情失败: %v\n", err)
		return nil, false
	}

	fmt.Printf("OCRResultCounterRecognition: 节点 %q 的结果 %q 连续出现 %d/%d 次，返回 true\n", recognitionNode, text, update.Count, targetCount)
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

func (r *OCRResultCounterRecognition) updateConsecutiveCount(node, text string) countUpdate {
	r.mu.Lock()
	defer r.mu.Unlock()

	update := countUpdate{
		PreviousNode:  r.lastNode,
		PreviousText:  r.lastText,
		PreviousCount: r.count,
		Consecutive:   r.lastNode == node && r.lastText == text,
	}
	if update.Consecutive {
		r.count++
		update.Count = r.count
		return update
	}

	r.lastNode = node
	r.lastText = text
	r.count = 1
	update.Count = r.count
	return update
}

func (r *OCRResultCounterRecognition) resetConsecutiveCount() counterState {
	r.mu.Lock()
	defer r.mu.Unlock()

	previous := counterState{
		Node:  r.lastNode,
		Text:  r.lastText,
		Count: r.count,
	}
	r.lastNode = ""
	r.lastText = ""
	r.count = 0
	return previous
}

func (r *OCRResultCounterRecognition) resetConsecutiveCountWithDebug(reason string) {
	previous := r.resetConsecutiveCount()
	fmt.Printf(
		"OCRResultCounterRecognition[DEBUG]: 连续计数已清零 reason=%q previous_node=%q previous_text=%q previous_count=%d\n",
		reason,
		previous.Node,
		previous.Text,
		previous.Count,
	)
}
