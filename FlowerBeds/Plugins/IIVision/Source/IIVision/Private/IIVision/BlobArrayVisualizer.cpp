#include "IIVision/BlobArrayVisualizer.h"

void UBlobArrayVisualizer::InitTexture(const int32 InWidth, const int32 InHeight)
{
	if (!Texture || Texture->GetSizeX() != InWidth || Texture->GetSizeY() != InHeight)
	{
		Width = InWidth;
		Height = InHeight;
		
		Texture = UTexture2D::CreateTransient(Width, Height, PF_B8G8R8A8);
		Texture->SRGB = false;
		Texture->Filter = TF_Nearest;
		Texture->MipGenSettings = TMGS_NoMipmaps;
		Texture->NeverStream = true;
		Texture->UpdateResource();

		Data.SetNumUninitialized(Width * Height);
		UpdateRegion = MakeUnique<FUpdateTextureRegion2D>(0, 0, 0, 0, Width, Height);
		
		if (OnInitialized.IsBound())
		{
			OnInitialized.Broadcast(Texture);
		}
	}
}

static FColor ColorForId(const uint32 Id)
{
	// Deterministic “random” color from id
	const uint32 x = Id * 2654435761u; // Knuth hash
	const uint8 r = static_cast<uint8>((x) & 0xFF);
	const uint8 g = static_cast<uint8>((x >> 8) & 0xFF);
	const uint8 b = static_cast<uint8>((x >> 16) & 0xFF);
	// avoid too-dark
	return FColor(FMath::Max<uint8>(r, 50), FMath::Max<uint8>(g, 50), FMath::Max<uint8>(b, 50), 255);
}

void UBlobArrayVisualizer::UpdateTexture(const TArray<II::Vision::FBlobTracker::FBlob2D>& Blobs)
{
	// Set texture to transparent
	for (FColor& Color : Data)
	{
		Color = FColor(0, 0, 0, 0);
	}
	
	for (const auto& Blob : Blobs)
	{
		DrawBlobRect(Blob, ColorForId(Blob.Id));
	}
	
	Texture->UpdateTextureRegions(
		0,
		1, 
		UpdateRegion.Get(), 
		Width * sizeof(FColor), 
		sizeof(FColor),
		reinterpret_cast<uint8*>(Data.GetData()));
}

void UBlobArrayVisualizer::PutPixel(const int32 X, const int32 Y, const FColor& Color)
{
	if (X >= 0 && X < Width && Y >= 0 && Y < Height)
	{
		Data[Y * Width + X] = Color;
	}
}

void UBlobArrayVisualizer::DrawBlobRect(const II::Vision::FBlobTracker::FBlob2D& Blob, const FColor& Color)
{
	constexpr int32 Thickness = 2;

	const int32 MinX = FMath::Clamp(Blob.MinX, 0, Width - 1);
	const int32 MaxX = FMath::Clamp(Blob.MaxX, 0, Width - 1);
	const int32 MinY = FMath::Clamp(Blob.MinY, 0, Height - 1);
	const int32 MaxY = FMath::Clamp(Blob.MaxY, 0, Height - 1);

	for (int32 t = 0; t < Thickness; ++t)
	{
		const int32 Y0 = FMath::Clamp(MinY + t, 0, Height - 1);
		const int32 Y1 = FMath::Clamp(MaxY - t, 0, Height - 1);

		for (int32 x = MinX; x <= MaxX; ++x)
		{
			PutPixel(x, Y0, Color); 
			PutPixel(x, Y1, Color);
		}

		const int32 X0 = FMath::Clamp(MinX + t, 0, Width - 1);
		const int32 X1 = FMath::Clamp(MaxX - t, 0, Width - 1);

		for (int32 y = MinY; y <= MaxY; ++y)
		{
			PutPixel(X0, y, Color); 
			PutPixel(X1, y, Color);
		}
	}
}


