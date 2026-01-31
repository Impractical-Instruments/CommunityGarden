#include "ArrayVisualizer.h"

#include "Rendering/Texture2DResource.h"

void UArrayVisualizer::InitTexture(int32 Width, int32 Height, EPixelFormat PF, bool bSRGB)
{
	if (!Texture || Texture->GetSizeX() != Width || Texture->GetSizeY() != Height || Texture->GetPixelFormat() != PF)
	{
		Texture = UTexture2D::CreateTransient(Width, Height, PF);
		Texture->SRGB = bSRGB;
		Texture->Filter = TF_Nearest;
		Texture->AddressX = TA_Clamp;
		Texture->AddressY = TA_Clamp;
		Texture->MipGenSettings = TMGS_NoMipmaps;
		Texture->NeverStream = true;
		Texture->UpdateResource();
		
		if (OnInitialized.IsBound())
		{
			OnInitialized.Broadcast(Texture);
		}
	}
}

void UArrayVisualizer::UpdateTexture(
	const uint8* Data, 
	int32 Width, 
	int32 Height,
	EPixelFormat PF)
{
	if (!Texture || !Texture->GetResource()) return;
	
	int32 TargetStride;
	
	switch (PF)
	{
	case PF_G8:
		TargetStride = 1;
		break;
	case PF_G16:
		TargetStride = 2;
		break;
	case PF_R8G8B8A8:
	case PF_B8G8R8A8:
		TargetStride = 4;
		break;
	default:
		UE_LOG(LogTemp, Warning, TEXT("Unsupported pixel format %d"), PF);
		return;
	}

	// Copy src into a buffer owned by the render command (lifetime safety)
	TArray<uint8> Copy;
	Copy.SetNumUninitialized(TargetStride * Width * Height);
	FMemory::Memcpy(Copy.GetData(), Data, Copy.Num());

	ENQUEUE_RENDER_COMMAND(UpdateOrbbecDebugTexture)(
	  [Texture = Texture, Width, Height, PitchBytes = TargetStride * Width, Copy = MoveTemp(Copy)](FRHICommandListImmediate& RHICmdList) mutable
	  {
		if (const auto* Res = static_cast<FTexture2DResource*>(Texture->GetResource()))
		{
		  const FUpdateTextureRegion2D Region(0, 0, 0, 0, Width, Height);
		  RHICmdList.UpdateTexture2D(Res->GetTexture2DRHI(), 0, Region, PitchBytes, Copy.GetData());
		}
	  });
}
