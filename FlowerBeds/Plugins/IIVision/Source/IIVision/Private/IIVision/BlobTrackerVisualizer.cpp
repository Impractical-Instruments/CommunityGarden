#include "IIVision/BlobTrackerVisualizer.h"

#include "Rendering/Texture2DResource.h"

void UBlobTrackerVisualizer::SetBackgroundDepthMap(const TArray<uint16>& DepthMap, int32 Width, int32 Height)
{
	if (!BackgroundDepthTexture || BackgroundDepthTexture->GetSizeX() != Width || BackgroundDepthTexture->GetSizeY() != Height)
	{
		BackgroundDepthTexture = UTexture2D::CreateTransient(Width, Height, PF_G16, "BlobTrackerBGDepthMap");
		BackgroundDepthTexture->SRGB = false;
		BackgroundDepthTexture->UpdateResource();
		OnBackgroundDepthTextureUpdated.Broadcast(BackgroundDepthTexture);
	}

	TArray<uint8> Copy;
	Copy.Append(reinterpret_cast<const uint8*>(DepthMap.GetData()), DepthMap.Num() * sizeof(uint16));
	
	ENQUEUE_RENDER_COMMAND(UpdateBlobTrackerBackgroundTexture)(
	  [Tex = BackgroundDepthTexture, Width, Height, Copy = MoveTemp(Copy)](FRHICommandListImmediate& RHICmdList) mutable
	  {
		if (const auto* Res = static_cast<FTexture2DResource*>(Tex->GetResource()))
		{
			const FUpdateTextureRegion2D Region(0, 0, 0, 0, Width, Height);
			RHICmdList.UpdateTexture2D(Res->GetTexture2DRHI(), 0, Region, Width * 2, Copy.GetData());
		}
	  });
}

void UBlobTrackerVisualizer::SetForegroundMask(const TArray<uint8>& Mask, int32 Width, int32 Height)
{
	if (!ForegroundMaskTexture || ForegroundMaskTexture->GetSizeX() != Width || ForegroundMaskTexture->GetSizeY() != Height)
	{
		ForegroundMaskTexture = UTexture2D::CreateTransient(Width, Height, PF_G8, "BlobTrackerFGMask");
		ForegroundMaskTexture->SRGB = false;
		ForegroundMaskTexture->CompressionSettings = TC_Grayscale;
		ForegroundMaskTexture->Filter = TF_Nearest;
		ForegroundMaskTexture->UpdateResource();
		OnForegroundTextureUpdated.Broadcast(ForegroundMaskTexture);
	}
	
	TArray<uint8> Copy;
	Copy.Append(Mask);
	
	ENQUEUE_RENDER_COMMAND(UpdateBlobTrackerForegroundTexture)(
	  [Tex = ForegroundMaskTexture, Width, Height, Copy = MoveTemp(Copy)](FRHICommandListImmediate& RHICmdList) mutable
	  {
		if (const auto* Res = static_cast<FTexture2DResource*>(Tex->GetResource()))
		{
			const FUpdateTextureRegion2D Region(0, 0, 0, 0, Width, Height);
			RHICmdList.UpdateTexture2D(Res->GetTexture2DRHI(), 0, Region, Width, Copy.GetData());
		}
	  });
}
