package my_recognizer

import (
	"fmt"

	"github.com/MaaXYZ/maa-framework-go/v4"
)

type MyRecognizer struct{}

// Run 自定义识别器
func (r *MyRecognizer) Run(ctx *maa.Context, arg *maa.CustomRecognitionArg) (*maa.CustomRecognitionResult, bool) {
	fmt.Println("成功注册MyRecognizer")
	return nil, false
}