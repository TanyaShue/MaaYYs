package ocrtext

import (
	"slices"
	"testing"

	"github.com/MaaXYZ/maa-framework-go/v4"
)

func TestNumber(t *testing.T) {
	tests := []struct {
		name   string
		texts  []string
		want   int
		wantOK bool
	}{
		{name: "纯数字", texts: []string{"12"}, want: 12, wantOK: true},
		{name: "零", texts: []string{"0"}, want: 0, wantOK: true},
		{name: "带后缀", texts: []string{"12人"}, want: 12, wantOK: true},
		{name: "带前后空格", texts: []string{" 7 "}, want: 7, wantOK: true},
		{name: "带前缀", texts: []string{"人数 7"}, want: 7, wantOK: true},
		{name: "全角数字", texts: []string{"１２"}, want: 12, wantOK: true},
		{name: "跳过无法解析的候选", texts: []string{"人数", "9"}, want: 9, wantOK: true},
		{name: "无数字", texts: []string{"无人", "人数"}, wantOK: false},
		{name: "空文本", texts: []string{""}, wantOK: false},
		{name: "空候选列表", texts: nil, wantOK: false},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, _, ok := Number(tt.texts)
			if ok != tt.wantOK || got != tt.want {
				t.Errorf("Number(%v) = (%d, %v), want (%d, %v)", tt.texts, got, ok, tt.want, tt.wantOK)
			}
		})
	}
}

func TestTextsOrderAndDedup(t *testing.T) {
	detail := &maa.RecognitionDetail{
		Results: &maa.RecognitionResults{},
		DetailJson: `{
			"all": [{"text": "噪声"}, {"text": "9"}],
			"filtered": [{"text": "9"}],
			"best": {"text": "9"}
		}`,
	}

	got := Texts(detail)
	want := []string{"9", "噪声"}
	if !slices.Equal(got, want) {
		t.Errorf("Texts() = %v, want %v", got, want)
	}

	if texts := Texts(nil); len(texts) != 0 {
		t.Errorf("Texts(nil) = %v, want 空", texts)
	}
}

// TestNumberFromDetailJson 复现识别成功但数值被写死的场景。
func TestNumberFromDetailJson(t *testing.T) {
	tests := []struct {
		name       string
		detailJson string
		wantValue  int
		wantOK     bool
	}{
		{
			name:       "expected 过滤命中",
			detailJson: `{"all":[{"text":"5"}],"filtered":[{"text":"5"}],"best":{"text":"5"}}`,
			wantValue:  5,
			wantOK:     true,
		},
		{
			name:       "best 没有数字时回退到 all",
			detailJson: `{"all":[{"text":"人数"},{"text":"9"}],"filtered":[],"best":{"text":"人数"}}`,
			wantValue:  9,
			wantOK:     true,
		},
		{
			name:       "带单位的识别结果",
			detailJson: `{"all":[{"text":"12人"}],"filtered":[],"best":{"text":"12人"}}`,
			wantValue:  12,
			wantOK:     true,
		},
		{
			name:       "完全没有数字",
			detailJson: `{"all":[{"text":"人数"}],"filtered":[],"best":null}`,
			wantOK:     false,
		},
		{
			name:       "空的识别详情",
			detailJson: `{}`,
			wantOK:     false,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			detail := &maa.RecognitionDetail{
				Results:    &maa.RecognitionResults{},
				DetailJson: tt.detailJson,
			}

			got, _, ok := Number(Texts(detail))
			if ok != tt.wantOK || got != tt.wantValue {
				t.Errorf("Number(Texts(detail)) = (%d, %v), want (%d, %v)", got, ok, tt.wantValue, tt.wantOK)
			}
		})
	}
}

func TestDescribe(t *testing.T) {
	if got := Describe(7, "7"); got != "7" {
		t.Errorf("Describe(7) = %q, want %q", got, "7")
	}
	if got := Describe(12, "12人"); got != `12 (OCR原始文本: "12人")` {
		t.Errorf("Describe(12人) = %q", got)
	}
}
