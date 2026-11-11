import os

import torch
from sklearn.metrics import (
    balanced_accuracy_score,
    classification_report,
    f1_score,
)

from car_fault_detection import config
from car_fault_detection import visualization as utils


def evaluate_model(model, loader, classes):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.eval()

    all_preds = []
    all_labels = []

    with torch.no_grad():
        for inputs, labels in loader:
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)
            _, predicted = outputs.max(1)

            all_preds.extend(predicted.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())

    bal_acc = balanced_accuracy_score(all_labels, all_preds)
    macro_f1 = f1_score(all_labels, all_preds, average="macro", zero_division=0)

    # Classification Report
    report = classification_report(all_labels, all_preds, target_names=classes, zero_division=0)
    print("\nClassification Report:")
    print(report)
    print(f"Balanced Accuracy: {bal_acc:.4f}")
    print(f"Macro F1: {macro_f1:.4f}")

    # Save report to file
    with open(os.path.join(config.RESULTS_DIR, "classification_report.txt"), "w") as f:
        f.write(report)
        f.write(f"\nBalanced Accuracy: {bal_acc:.4f}\n")
        f.write(f"Macro F1: {macro_f1:.4f}\n")

    # Plot Confusion Matrix
    utils.plot_confusion_matrix(
        all_labels,
        all_preds,
        classes,
        save_path=os.path.join(config.RESULTS_DIR, "confusion_matrix.png"),
    )

    return all_labels, all_preds
