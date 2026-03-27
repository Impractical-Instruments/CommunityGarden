#pragma once

#include "CoreMinimal.h"

#include "TouchScreen.generated.h"

struct FOrbbecFrame;
class UOrbbecCameraController;

/**
 * Identifies a single cell in the touch grid by its zero-based row and column.
 * Row 0 is the top of the screen; Col 0 is the left.
 */
USTRUCT(BlueprintType)
struct FScreenGridCell
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Touch Screen")
	int32 Row = 0;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Touch Screen")
	int32 Col = 0;

	bool operator==(const FScreenGridCell& Other) const
	{
		return Row == Other.Row && Col == Other.Col;
	}
};

/**
 * Fired when a grid cell transitions from untouched to touched.
 * NormalisedPos is the [0,1]x[0,1] position within the screen (origin top-left).
 */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_TwoParams(
	FOnCellTouched,
	FScreenGridCell, Cell,
	FVector2D, NormalisedPos);

/**
 * Fired when a previously-touched grid cell is no longer touched.
 */
DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(
	FOnCellReleased,
	FScreenGridCell, Cell);

/**
 * Actor representing a depth-camera-backed touch screen.
 *
 * The actor transform tracks the Orbbec camera that observes the screen.
 * The physical screen surface is a separate plane defined by ScreenTransform,
 * ScreenWidthCm, and ScreenHeightCm (populated from UTouchScreenSettings at BeginPlay).
 *
 * The screen surface is divided into a dynamic grid whose dimensions are set by
 * calling SetGrid() before each CAPTCHA challenge. Touch events are broadcast via
 * OnCellTouched and OnCellReleased.
 *
 * Place a BP_TouchScreen (Blueprint subclass) in the level and set ScreenName to
 * match the corresponding entry in Project Settings → Touch Screen Settings.
 */
UCLASS(ClassGroup = (FlowerBeds))
class ATouchScreen : public AActor
{
	GENERATED_BODY()

public:
	/**
	 * Matches this actor against FTouchScreenConfig::Name in UTouchScreenSettings.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Touch Screen")
	FName ScreenName = NAME_None;

	/**
	 * Reconfigure the grid dimensions. Clears any currently-touched cells and fires
	 * release events for them. Call this before presenting each new CAPTCHA challenge.
	 */
	UFUNCTION(BlueprintCallable, Category = "Touch Screen")
	void SetGrid(int32 Rows, int32 Cols);

	UFUNCTION(BlueprintPure, Category = "Touch Screen")
	int32 GetGridRows() const { return GridRows; }

	UFUNCTION(BlueprintPure, Category = "Touch Screen")
	int32 GetGridCols() const { return GridCols; }

	/** Fired when a cell transitions from untouched → touched. */
	UPROPERTY(BlueprintAssignable, Category = "Touch Screen")
	FOnCellTouched OnCellTouched;

	/** Fired when a cell transitions from touched → untouched. */
	UPROPERTY(BlueprintAssignable, Category = "Touch Screen")
	FOnCellReleased OnCellReleased;

	ATouchScreen();
	virtual void BeginPlay() override;
	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

private:
	int32 GridRows = 3;
	int32 GridCols = 3;

	// Screen plane geometry, populated from config at BeginPlay.
	FTransform ScreenTransform;
	float ScreenWidthCm = 0.f;
	float ScreenHeightCm = 0.f;
	float TouchThresholdCm = 5.f;

	// Set of currently-touched cells, encoded as (Row * GridCols + Col).
	TSet<int32> TouchedCellIndices;

	UPROPERTY(Transient)
	TObjectPtr<UOrbbecCameraController> CameraController;

	FDelegateHandle OnFramesReceivedDelegateHandle;

	void OnFramesReceived(
		const FOrbbecFrame& ColorFrame,
		const FOrbbecFrame& DepthFrame,
		const FOrbbecFrame& IRFrame);

	/**
	 * Projects depth-frame pixels onto the screen plane and returns the normalised
	 * [0,1]x[0,1] screen-space positions of detected touch candidates.
	 *
	 * TODO: Implement.
	 *
	 * Suggested approach:
	 *   1. For each depth pixel (px, py) with valid depth Z (mm):
	 *        - Unproject to camera space using depth intrinsics:
	 *            X_cam = (px - Cx) * Z / Fx
	 *            Y_cam = (py - Cy) * Z / Fy
	 *            Z_cam = Z
	 *          (Cx, Cy, Fx, Fy available from CameraController->CameraConfig.DepthConfig)
	 *        - Transform to world space using GetActorTransform() (camera transform).
	 *   2. Compute the signed distance from the world point to the screen plane:
	 *        dist = dot(worldPoint - ScreenTransform.GetLocation(), ScreenTransform.GetUnitAxis(EAxis::X))
	 *   3. If 0 <= dist <= TouchThresholdCm, the point is a touch candidate in front of the screen.
	 *   4. Project the world point onto the screen plane and compute normalised UV coords:
	 *        U = dot(localPoint, ScreenTransform.GetUnitAxis(EAxis::Y)) / ScreenWidthCm  + 0.5
	 *        V = -dot(localPoint, ScreenTransform.GetUnitAxis(EAxis::Z)) / ScreenHeightCm + 0.5
	 *   5. If U and V are in [0, 1], add FVector2D(U, V) to OutNormalisedTouches.
	 *   6. Cluster nearby candidates (similar to FBlobTracker::ExtractBlobs) to collapse
	 *      multiple pixels from the same finger into a single touch point.
	 */
	void DetectTouches(const FOrbbecFrame& DepthFrame, TArray<FVector2D>& OutNormalisedTouches) const;

	/**
	 * Maps a normalised [0,1]x[0,1] screen position to a grid cell.
	 * Returns false if the position is outside the screen bounds.
	 */
	bool NormalisedPosToCell(const FVector2D& NormPos, FScreenGridCell& OutCell) const;

	/**
	 * Reconciles the new touch positions against the previous frame's touched cells
	 * and fires OnCellTouched / OnCellReleased as appropriate.
	 */
	void UpdateTouchedCells(const TArray<FVector2D>& NormalisedTouches);
};
