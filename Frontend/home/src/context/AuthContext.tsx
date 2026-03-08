// import React, { createContext, useContext } from 'react';

// const AuthContext = createContext<{ user: { name: string } | null }>({ user: null });

// export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
//   const storedUser = localStorage.getItem('ffte_user');
//   let user = null;
//   if (storedUser) {
//     try {
//       const parsed = JSON.parse(storedUser);
//       if (parsed && parsed.loggedIn) {
//         user = { name: parsed.username };
//       }
//     } catch (e) {}
//   }

//   return (
//     <AuthContext.Provider value={{ user }}>
//       {children}
//     </AuthContext.Provider>
//   );
// };

// export const useAuth = () => useContext(AuthContext);
