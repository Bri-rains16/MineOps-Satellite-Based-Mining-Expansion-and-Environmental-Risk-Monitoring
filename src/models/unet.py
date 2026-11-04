import torch
import torch.nn as nn
import segmentation_models_pytorch as smp

def build_model(in_channels=3):
    return smp.Unet(
        encoder_name="resnet34",
        encoder_weights=None,
        in_channels=in_channels,
        classes=1
    )

def adapt_input_channels(model, new_channels=10):
    old_conv = model.encoder.conv1
    
    new_conv = nn.Conv2d(
        in_channels=new_channels,
        out_channels=old_conv.out_channels,
        kernel_size=old_conv.kernel_size,
        stride=old_conv.stride,
        padding=old_conv.padding,
        bias=old_conv.bias is not None
    )
    
    with torch.no_grad():
        # Copy the learned RGB weights into the first 3 channels
        new_conv.weight[:, :3, :, :] = old_conv.weight
        # Initialize the 7 new Sentinel-2 channels with the average of the RGB weights
        rgb_mean = old_conv.weight.mean(dim=1, keepdim=True)
        for i in range(3, new_channels):
            new_conv.weight[:, i:i+1, :, :] = rgb_mean
            
    model.encoder.conv1 = new_conv
    return model

if __name__ == "__main__":
    unet = build_model(in_channels=3)
    print(f"Original input channels: {unet.encoder.conv1.in_channels}")
    unet = adapt_input_channels(unet, new_channels=10)
    print(f"Adapted input channels: {unet.encoder.conv1.in_channels}")