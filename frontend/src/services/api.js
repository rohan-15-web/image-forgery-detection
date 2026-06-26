export const analyzeImage = async (file) => {
  const formData = new FormData();
  formData.append('image', file);

  const response = await fetch('/api/predict', {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    const err = await response.json();
    throw new Error(err.error || 'Prediction failed');
  }

  return response.json();
};
