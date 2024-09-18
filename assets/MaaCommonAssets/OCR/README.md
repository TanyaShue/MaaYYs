
# OCR

Awesome multilingual OCR toolkits based on PaddlePaddle (practical ultra lightweight OCR system, support 80+ languages recognition, provide data annotation and synthesis tools, support training and deployment among server, mobile, embedded and IoT devices)  

<https://github.com/PaddlePaddle/PaddleOCR>

## command

### det

```bash
paddle2onnx --model_dir . --model_filename inference.pdmodel --params_filename inference.pdiparams --save_file det_unopt.onnx --opset_version 16 --enable_dev_version True --enable_onnx_checker True --deploy_backend onnxruntime
```

```bash
python -m paddle2onnx.optimize --input_model det_unopt.onnx --output_model det.onnx
```

### rec

```bash
paddle2onnx --model_dir . --model_filename inference.pdmodel --params_filename inference.pdiparams --save_file rec_unopt.onnx --opset_version 16 --enable_dev_version True --enable_onnx_checker True --deploy_backend onnxruntime
```

```bash
python -m paddle2onnx.optimize --input_model rec_unopt.onnx --output_model rec.onnx
```
