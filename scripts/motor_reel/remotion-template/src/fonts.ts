import {useEffect, useState} from 'react';
import {cancelRender, continueRender, delayRender, staticFile} from 'remotion';

let loaded = false;

export const useFonts = () => {
  const [handle] = useState(() => delayRender('fonts'));
  useEffect(() => {
    if (loaded) {
      continueRender(handle);
      return;
    }
    const faces = [
      new FontFace('Archivo Black', `url(${staticFile('fonts/ArchivoBlack-Regular.ttf')})`, {weight: '400'}),
      new FontFace('Poppins', `url(${staticFile('fonts/Poppins-Bold.ttf')})`, {weight: '700'}),
      new FontFace('Poppins', `url(${staticFile('fonts/Poppins-Black.ttf')})`, {weight: '900'}),
    ];
    Promise.all(faces.map((f) => f.load()))
      .then((ready) => {
        ready.forEach((f) => document.fonts.add(f));
        loaded = true;
        continueRender(handle);
      })
      .catch((err) => cancelRender(err));
  }, [handle]);
};
