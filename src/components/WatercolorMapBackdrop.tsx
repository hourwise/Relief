import React from 'react';
import { StyleSheet, View } from 'react-native';
import Svg, { Defs, Ellipse, Line, LinearGradient, Rect, Stop } from 'react-native-svg';

/** Decorative startup-only map. It is never used above the live facility map. */
export const WatercolorMapBackdrop: React.FC = () => (
  <View pointerEvents="none" style={StyleSheet.absoluteFill}>
    <Svg width="100%" height="100%" viewBox="0 0 390 800" preserveAspectRatio="xMidYMid slice">
      <Defs>
        <LinearGradient id="reliefWatercolor" x1="0" y1="0" x2="1" y2="1">
          <Stop offset="0" stopColor="#B9DDD1" />
          <Stop offset="0.54" stopColor="#E4F0EA" />
          <Stop offset="1" stopColor="#9FCDBE" />
        </LinearGradient>
      </Defs>
      <Rect width="390" height="800" fill="url(#reliefWatercolor)" />
      {[36, 98, 166, 238, 310, 370].map((x) => <Line key={`v-${x}`} x1={x} y1="0" x2={x + 45} y2="800" stroke="#8CB8AA" strokeWidth="8" opacity="0.36" strokeLinecap="round" />)}
      {[68, 164, 264, 370, 484, 606, 720].map((y) => <Line key={`h-${y}`} x1="0" y1={y} x2="390" y2={y + 24} stroke="#8CB8AA" strokeWidth="7" opacity="0.32" strokeLinecap="round" />)}
      <Line x1="-20" y1="170" x2="410" y2="560" stroke="#6FAE9A" strokeWidth="10" opacity="0.26" strokeLinecap="round" />
      <Line x1="360" y1="20" x2="18" y2="770" stroke="#6FAE9A" strokeWidth="6" opacity="0.23" strokeLinecap="round" />
      <Ellipse cx="70" cy="128" rx="94" ry="72" fill="#75AF99" opacity="0.22" />
      <Ellipse cx="322" cy="235" rx="88" ry="68" fill="#8DBF9E" opacity="0.25" />
      <Ellipse cx="205" cy="548" rx="122" ry="84" fill="#75AD96" opacity="0.18" />
      <Ellipse cx="50" cy="710" rx="92" ry="76" fill="#79B89A" opacity="0.24" />
    </Svg>
  </View>
);
