package ocr_result_counter_recognition

import (
	"testing"

	maa "github.com/MaaXYZ/maa-framework-go/v4"
)

func TestParseParamsAcceptsNumberAndNumericString(t *testing.T) {
	tests := []struct {
		name string
		raw  string
		want int
	}{
		{name: "number", raw: `{"recognition_node":"OCR节点","target_count":3}`, want: 3},
		{name: "numeric string", raw: `{"recognition_node":"OCR节点","target_count":"4"}`, want: 4},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			node, count, err := parseParams(tc.raw)
			if err != nil {
				t.Fatalf("parseParams() error = %v", err)
			}
			if node != "OCR节点" || count != tc.want {
				t.Fatalf("parseParams() = (%q, %d), want (%q, %d)", node, count, "OCR节点", tc.want)
			}
		})
	}
}

func TestParseParamsRejectsInvalidTargetCount(t *testing.T) {
	tests := []string{
		`{"recognition_node":"OCR节点","target_count":0}`,
		`{"recognition_node":"OCR节点","target_count":1.5}`,
		`{"recognition_node":"OCR节点","target_count":"abc"}`,
		`{"recognition_node":"OCR节点"}`,
	}

	for _, raw := range tests {
		if _, _, err := parseParams(raw); err == nil {
			t.Fatalf("parseParams(%s) error = nil", raw)
		}
	}
}

func TestBestOCRResultFromDetailJSON(t *testing.T) {
	detail := &maa.RecognitionDetail{
		DetailJson: `{"best":{"box":[1,2,3,4],"text":"  识别文本  ","score":0.99}}`,
	}

	text, box, ok := bestOCRResult(detail)
	if !ok {
		t.Fatal("bestOCRResult() ok = false")
	}
	if text != "识别文本" {
		t.Fatalf("bestOCRResult() text = %q", text)
	}
	if box != (maa.Rect{1, 2, 3, 4}) {
		t.Fatalf("bestOCRResult() box = %v", box)
	}
}

func TestBestOCRResultRejectsMissingBest(t *testing.T) {
	for _, detailJSON := range []string{`{}`, `{"best":null}`, `{"best":{"text":" "}}`} {
		if _, _, ok := bestOCRResult(&maa.RecognitionDetail{DetailJson: detailJSON}); ok {
			t.Fatalf("bestOCRResult(%s) ok = true", detailJSON)
		}
	}
}

func TestUpdateConsecutiveCount(t *testing.T) {
	r := &OCRResultCounterRecognition{}
	if got := r.updateConsecutiveCount("节点A", "文本A"); got.Count != 1 || got.Consecutive {
		t.Fatalf("first update = %+v, want count 1 and non-consecutive", got)
	}
	if got := r.updateConsecutiveCount("节点A", "文本A"); got.Count != 2 || !got.Consecutive {
		t.Fatalf("second update = %+v, want count 2 and consecutive", got)
	}
	if got := r.updateConsecutiveCount("节点A", "文本B"); got.Count != 1 || got.Consecutive {
		t.Fatalf("changed text update = %+v, want count 1 and non-consecutive", got)
	}
	if got := r.updateConsecutiveCount("节点A", "文本A"); got.Count != 1 || got.Consecutive {
		t.Fatalf("previous text after interruption update = %+v, want count 1 and non-consecutive", got)
	}
	if got := r.updateConsecutiveCount("节点B", "文本A"); got.Count != 1 || got.Consecutive {
		t.Fatalf("changed node update = %+v, want count 1 and non-consecutive", got)
	}
	if got := r.updateConsecutiveCount("节点B", "文本A"); got.Count != 2 || !got.Consecutive {
		t.Fatalf("same text on same node update = %+v, want count 2 and consecutive", got)
	}
	previous := r.resetConsecutiveCount()
	if previous.Node != "节点B" || previous.Text != "文本A" || previous.Count != 2 {
		t.Fatalf("reset previous state = %+v", previous)
	}
	if got := r.updateConsecutiveCount("节点B", "文本A"); got.Count != 1 || got.Consecutive {
		t.Fatalf("update after failed recognition reset = %+v, want count 1 and non-consecutive", got)
	}
}
