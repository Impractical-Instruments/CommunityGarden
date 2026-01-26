#include "OrbbecSensor/Visualization/OrbbecDebugTexture.h"

#include "RHICommandList.h"
#include "Engine/Texture2D.h"
#include "OrbbecSensor/Device/OrbbecCameraController.h"
#include "Rendering/Texture2DResource.h"

void UOrbbecDebugTexture::UpdateTexture(const FOrbbecFrame& Frame)
{
	if (Frame.Config.Width <= 0 || Frame.Config.Height <= 0 || Frame.Data.Num() <= 0)
	{
		return;
	}
	
	const auto W = Frame.Config.Width;
	const auto H = Frame.Config.Height;
	
	switch (Frame.Config.Format)
	{
	case EOrbbecFrameFormat::Y16:
		EnsureTexture(W, H, PF_G16, false);
		UpdateTexture(Texture, W, H, Frame.Data, 2, 2);
		break;
	case EOrbbecFrameFormat::RGB:
		EnsureTexture(W, H, PF_R8G8B8A8, true);
		UpdateTexture(Texture, W, H, Frame.Data, 3, 4);
		break;
	case EOrbbecFrameFormat::BGR:
		EnsureTexture(W, H, PF_B8G8R8A8, true);
		UpdateTexture(Texture, W, H, Frame.Data, 3, 4);
		break;
	case EOrbbecFrameFormat::BGRA:
		EnsureTexture(W, H, PF_B8G8R8A8, true);
		UpdateTexture(Texture, W, H, Frame.Data, 4, 4);
		break;
	case EOrbbecFrameFormat::RGBA:
		EnsureTexture(W, H, PF_R8G8B8A8, true);
		UpdateTexture(Texture, W, H, Frame.Data, 4, 4);
		break;
	case EOrbbecFrameFormat::YUYV:
	case EOrbbecFrameFormat::MJPG:
	case EOrbbecFrameFormat::Unknown:
		break;
	}
}

void UOrbbecDebugTexture::EnsureTexture(int32 W, int32 H, EPixelFormat PF, bool bSRGB)
{
	if (!Texture || Texture->GetSizeX() != W || Texture->GetSizeY() != H || Texture->GetPixelFormat() != PF)
	{
		Texture = UTexture2D::CreateTransient(W, H, PF);
		Texture->SRGB = bSRGB;
		Texture->UpdateResource();
		
		if (OnInitialized.IsBound())
		{
			OnInitialized.Broadcast(Texture);
		}
	}
}

void UOrbbecDebugTexture::UpdateTexture(
	UTexture2D* Tex, 
	int32 W, 
	int32 H, 
	const TArray<uint8>& Data, 
	int32 SrcStride,
	int32 TargetStride)
{
	if (!Tex || !Tex->GetResource()) return;
	
	if (Data.Num() != W * H * SrcStride) return;

	// Copy src into a buffer owned by the render command (lifetime safety)
	TArray<uint8> Copy;
	Copy.SetNumUninitialized(TargetStride * W * H);
	
	if (SrcStride == TargetStride)
	{
		FMemory::Memcpy(Copy.GetData(), Data.GetData(), Copy.Num());
	}
	else
	{
		for (int32 Pixel = 0; Pixel < W * H; ++Pixel)
		{
			const auto SrcIndex = Pixel * SrcStride;
			const auto TargetIndex = Pixel * TargetStride;
			Copy[TargetIndex] = Data[SrcIndex];
		}
	}

	ENQUEUE_RENDER_COMMAND(UpdateOrbbecDebugTexture)(
	  [Tex, W, H, PitchBytes = TargetStride * W, Copy = MoveTemp(Copy)](FRHICommandListImmediate& RHICmdList) mutable
	  {
		if (const auto* Res = static_cast<FTexture2DResource*>(Tex->GetResource()))
		{
		  const FUpdateTextureRegion2D Region(0, 0, 0, 0, W, H);
		  RHICmdList.UpdateTexture2D(Res->GetTexture2DRHI(), 0, Region, PitchBytes, Copy.GetData());
		}
	  });
}
