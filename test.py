import requests
from PIL import Image, ImageDraw
from transformers import AutoProcessor, AutoModelForCausalLM 
import os

def process_image(input_image_path):
    # model = AutoModelForCausalLM.from_pretrained("yifeihu/TFT-ID-1.0", trust_remote_code=True)
    
    model = AutoModelForCausalLM.from_pretrained("yifeihu/TF-ID-large-no-caption", trust_remote_code=True)
    
    processor = AutoProcessor.from_pretrained("yifeihu/TFT-ID-1.0", trust_remote_code=True)

    prompt = "<OD>"
    image = Image.open(input_image_path)

    inputs = processor(text=prompt, images=image, return_tensors="pt")

    generated_ids = model.generate(
        input_ids=inputs["input_ids"],
        pixel_values=inputs["pixel_values"],
        max_new_tokens=1024,
        do_sample=False,
        num_beams=3
    )
    generated_text = processor.batch_decode(generated_ids, skip_special_tokens=False)[0]

    parsed_answer = processor.post_process_generation(generated_text, task="<OD>", image_size=(image.width, image.height))

    print(parsed_answer)

    def draw_boxes(image_path, boxes_data, output_path):
        image = Image.open(image_path)
        draw = ImageDraw.Draw(image, 'RGBA')

        colors = {
            'text': (0, 0, 255, 64),
            'figure': (255, 165, 0, 64)
        }

        for box, label in zip(boxes_data['<OD>']['bboxes'], boxes_data['<OD>']['labels']):
            draw.rectangle(box, fill=colors[label], outline=colors[label][:3] + (255,), width=3)

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        image.save(output_path)

    input_filename = os.path.basename(input_image_path)
    output_filename = os.path.splitext(input_filename)[0] + "_with_boxes.png"
    output_image_path = os.path.join("data/output", output_filename)
    draw_boxes(input_image_path, parsed_answer, output_image_path)

    print(f"Image with bounding boxes saved to {output_image_path}")
    return output_image_path

# Example usage:
output_path = process_image("data/png/example1-2.png")
